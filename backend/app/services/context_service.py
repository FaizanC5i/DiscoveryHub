"""
Business rules for project documents.

Upload, in order:
1. Confirm the project belongs to the caller (404 otherwise).
2. Check the type, content, and size.
3. Save the original file to Blob Storage under a random key.
4. Extract text (OCR for PDF and images).
5. Save the source row and the content row in one transaction.

If anything after step 3 fails, the blob is deleted so nothing is orphaned.
A recognition failure is not a crash: the source is kept as "failed" with a
reason, so the user can press Retry without uploading the file again.
"""

import logging
import uuid
from pathlib import PurePosixPath

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.core.file_types import FileKind, basename, check_content, resolve_kind
from app.core.time import utc_now
from app.db.models import ContextContent, ContextSource, Project, User
from app.services.extraction.extractors import Extraction, ExtractionError, extract_text
from app.services.storage.blob_storage import BlobNotFound, BlobStorage

log = logging.getLogger(__name__)

TITLE_MAX_LENGTH = 255
FILENAME_MAX_LENGTH = 255
FAILURE_REASON_MAX_LENGTH = 500


def upload_source(
    db: Session,
    storage: BlobStorage,
    owner: User,
    project_id: int,
    filename: str,
    data: bytes,
) -> ContextSource:
    _require_project(db, owner.id, project_id)
    kind = resolve_kind(filename)
    check_content(kind, data)

    blob_key = f"projects/{project_id}/sources/{uuid.uuid4().hex}{kind.extension}"
    storage.save(blob_key, data, kind.mime_type)

    try:
        extraction, reason = _run_extraction(kind, data)
        source = ContextSource(
            project_id=project_id,
            created_by=owner.id,
            title=_title_from(filename),
            original_filename=basename(filename)[:FILENAME_MAX_LENGTH],
            blob_path=blob_key,
            mime_type=kind.mime_type,
            file_size_bytes=len(data),
            processing_status="processing",
        )
        _apply_result(source, extraction, reason)
        db.add(source)
        db.commit()
    except Exception:
        db.rollback()
        storage.delete(blob_key)
        raise

    return source


def list_sources(db: Session, owner_id: int, project_id: int) -> list[ContextSource]:
    _require_project(db, owner_id, project_id)
    statement = (
        select(ContextSource)
        .where(ContextSource.project_id == project_id, ContextSource.deleted_at.is_(None))
        .order_by(ContextSource.created_at.desc(), ContextSource.id.desc())
    )
    return list(db.scalars(statement))


def reprocess_source(
    db: Session,
    storage: BlobStorage,
    owner_id: int,
    project_id: int,
    source_id: int,
) -> ContextSource:
    """Run extraction again on the stored original. Used by the Retry button."""
    source = _get_source(db, owner_id, project_id, source_id)
    kind = resolve_kind(source.original_filename)

    try:
        data = storage.read(source.blob_path)
    except BlobNotFound:
        raise api_error(
            409,
            "BLOB_MISSING",
            "The original file is no longer stored. Please upload it again.",
        ) from None

    extraction, reason = _run_extraction(kind, data)
    _apply_result(source, extraction, reason)
    db.commit()
    return source


def delete_source(
    db: Session,
    storage: BlobStorage,
    owner_id: int,
    project_id: int,
    source_id: int,
) -> None:
    """Soft delete. The row is hidden at once; the blob is removed best-effort."""
    source = _get_source(db, owner_id, project_id, source_id)
    source.deleted_at = utc_now()
    db.commit()

    try:
        storage.delete(source.blob_path)
    except Exception:
        log.warning("Could not delete blob %s", source.blob_path, exc_info=True)


# --- helpers -----------------------------------------------------------------


def _run_extraction(kind: FileKind, data: bytes) -> tuple[Extraction | None, str | None]:
    """Return (text, None) on success or (None, reason) when the user can fix the file."""
    try:
        return extract_text(kind, data), None
    except ExtractionError as exc:
        return None, str(exc)


def _apply_result(
    source: ContextSource,
    extraction: Extraction | None,
    reason: str | None,
) -> None:
    """Set the status and content of a source from an extraction result."""
    if extraction is None:
        source.processing_status = "failed"
        source.failure_reason = (reason or "Text could not be extracted.")[:FAILURE_REASON_MAX_LENGTH]
        source.content = None  # delete-orphan removes any old text
        return

    source.processing_status = "ready"
    source.failure_reason = None
    if source.content is None:
        source.content = ContextContent(
            content_text=extraction.text,
            extraction_method=extraction.method,
        )
    else:
        source.content.content_text = extraction.text
        source.content.extraction_method = extraction.method


def _get_source(db: Session, owner_id: int, project_id: int, source_id: int) -> ContextSource:
    _require_project(db, owner_id, project_id)
    source = db.scalar(
        select(ContextSource).where(
            ContextSource.id == source_id,
            ContextSource.project_id == project_id,
            ContextSource.deleted_at.is_(None),
        )
    )
    if source is None:
        raise api_error(404, "SOURCE_NOT_FOUND", "Document not found.")
    return source


def _require_project(db: Session, owner_id: int, project_id: int) -> None:
    exists = db.scalar(
        select(Project.id).where(Project.id == project_id, Project.owner_id == owner_id)
    )
    if exists is None:
        raise api_error(404, "PROJECT_NOT_FOUND", "Project not found")


def _title_from(filename: str) -> str:
    stem = PurePosixPath(basename(filename)).stem
    return (stem or "Untitled document")[:TITLE_MAX_LENGTH]