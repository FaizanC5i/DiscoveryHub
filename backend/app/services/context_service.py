"""
Business rules for project documents.

Upload, in order:
1. Confirm the project belongs to the caller (404 otherwise).
2. Check the type, content, and size.
3. Save the original file to Blob Storage under a random key.
4. Extract text (OCR for PDF and images).
5. Save the source row and the content row in one transaction.
6. Split the text into chunks and save them (see context_chunk_service).

If anything after step 3 fails, the blob is deleted so nothing is orphaned.
A recognition failure is not a crash: the source is kept as "failed" with a
reason, so the user can press Retry without uploading the file again.
"""

import logging
import uuid
from dataclasses import dataclass
from pathlib import PurePosixPath

from sqlalchemy import select, true, update
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.core.file_types import FileKind, basename, check_content, resolve_kind
from app.core.time import utc_now
from app.db.models import (
    ContextChunk,
    ContextCheckpointMapping,
    ContextContent,
    ContextSource,
    Project,
    User,
)
from app.services import context_chunk_service
from app.services.extraction.extractors import Extraction, ExtractionError, extract_text
from app.services.storage.blob_storage import BlobNotFound, BlobStorage

log = logging.getLogger(__name__)

TITLE_MAX_LENGTH = 255
FILENAME_MAX_LENGTH = 255
FAILURE_REASON_MAX_LENGTH = 500
NOTE_TITLE_MAX_LENGTH = 255
NOTE_BODY_MAX_LENGTH = 12000
MANUAL_NOTE = "MANUAL_NOTE"
NOTE_MIME_TYPE = "text/plain"
NOTE_EXTRACTION_METHOD = "manual"


@dataclass(frozen=True)
class NoteDetails:
    source: ContextSource
    content: ContextContent
    chunk_count: int
    created_by_name: str


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

    if source.content is not None:
        context_chunk_service.chunk_uploaded_content(db, source.content, source)
    return source


def list_sources(
    db: Session,
    owner_id: int,
    project_id: int,
    query: str | None = None,
) -> list[ContextSource]:
    """
    Files and notes of a project, newest first. A query matches titles, file names
    and note text in the database, so the full text never has to reach the browser.
    """
    _require_project(db, owner_id, project_id)
    statement = (
        select(ContextSource)
        .outerjoin(ContextContent, ContextContent.context_source_id == ContextSource.id)
        .where(ContextSource.project_id == project_id, ContextSource.deleted_at.is_(None))
        .order_by(ContextSource.created_at.desc(), ContextSource.id.desc())
    )
    needle = (query or "").strip()
    if needle:
        statement = statement.where(
            ContextSource.title.contains(needle, autoescape=True)
            | ContextSource.original_filename.contains(needle, autoescape=True)
            | ContextContent.content_text.contains(needle, autoescape=True)
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
    if source.source_type == MANUAL_NOTE:
        # A note's text is already stored, so retrying only means chunking it again.
        if source.content is not None:
            context_chunk_service.chunk_uploaded_content(db, source.content, source)
        return source

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
    # Chunks point at exact characters of the stored text. If the text would change
    # (or disappear) under existing chunks, refuse rather than leave them pointing at the wrong words.
    if source.content is not None and context_chunk_service.has_chunks(db, source.content.id):
        if extraction is None or extraction.text != source.content.content_text:
            raise api_error(
                409,
                "CONTENT_HAS_CHUNKS",
                "This document's text has already been chunked and would change. Upload it again as a new document.",
            )
    _apply_result(source, extraction, reason)
    db.commit()
    if source.content is not None:
        context_chunk_service.chunk_uploaded_content(db, source.content, source)
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
    if source.content is not None:
        _deactivate_mappings(db, source.content.id)
    db.commit()

    if source.blob_path is None:
        return
    try:
        storage.delete(source.blob_path)
    except Exception:
        log.warning("Could not delete blob %s", source.blob_path, exc_info=True)


def sources_still_mapping(db: Session, source_ids: list[int]) -> set[int]:
    """Sources with at least one chunk the helper agent has not finished with yet."""
    if not source_ids:
        return set()
    rows = db.scalars(
        select(ContextContent.context_source_id)
        .join(ContextChunk, ContextChunk.context_content_id == ContextContent.id)
        .where(
            ContextContent.context_source_id.in_(source_ids),
            ContextChunk.mapping_status.in_(("PENDING", "IN_PROGRESS")),
        )
        .distinct()
    )
    return set(rows)


def create_note(db: Session, owner: User, project_id: int, title: str, body: str) -> ContextSource:
    _require_project(db, owner.id, project_id)
    source = ContextSource(
        project_id=project_id,
        created_by=owner.id,
        source_type=MANUAL_NOTE,
        title=_clean_title(title),
        mime_type=NOTE_MIME_TYPE,
        file_size_bytes=len(body.encode("utf-8")),
        processing_status="processing",
        content=ContextContent(content_text=body, extraction_method=NOTE_EXTRACTION_METHOD),
    )
    db.add(source)
    db.commit()

    context_chunk_service.chunk_uploaded_content(db, source.content, source)
    return source


def get_note(db: Session, owner_id: int, project_id: int, source_id: int) -> NoteDetails:
    source = _get_note(db, owner_id, project_id, source_id)
    content = source.content
    if content is None:
        raise api_error(404, "NOTE_NOT_FOUND", "Note not found.")
    creator = db.get(User, source.created_by)
    return NoteDetails(
        source=source,
        content=content,
        chunk_count=len(context_chunk_service.chunk_ids_for_content(db, content.id)),
        created_by_name=creator.name if creator else "",
    )


def update_note(
    db: Session,
    owner_id: int,
    project_id: int,
    source_id: int,
    title: str,
    body: str,
) -> ContextSource:
    """
    Change a note's title and/or text. Changing the text makes a new source row with its
    own chunks, and the old row is soft-deleted with its mappings deactivated. Chunks are
    never edited in place, so an old mapping can never point at different words.
    """
    source = _get_note(db, owner_id, project_id, source_id)
    content = source.content
    if content is None:
        raise api_error(404, "NOTE_NOT_FOUND", "Note not found.")

    new_title = _clean_title(title)
    if body == content.content_text:
        source.title = new_title
        source.updated_at = utc_now()
        db.commit()
        return source

    _deactivate_mappings(db, content.id)
    now = utc_now()
    replacement = ContextSource(
        project_id=project_id,
        created_by=source.created_by,
        source_type=MANUAL_NOTE,
        title=new_title,
        mime_type=NOTE_MIME_TYPE,
        file_size_bytes=len(body.encode("utf-8")),
        processing_status="processing",
        updated_at=now,
        content=ContextContent(content_text=body, extraction_method=NOTE_EXTRACTION_METHOD),
    )
    source.deleted_at = now
    db.add(replacement)
    db.commit()

    context_chunk_service.chunk_uploaded_content(db, replacement.content, replacement)
    return replacement


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


def _get_note(db: Session, owner_id: int, project_id: int, source_id: int) -> ContextSource:
    source = _get_source(db, owner_id, project_id, source_id)
    if source.source_type != MANUAL_NOTE:
        raise api_error(404, "NOTE_NOT_FOUND", "Note not found.")
    return source


def _deactivate_mappings(db: Session, content_id: int) -> None:
    chunk_ids = select(ContextChunk.id).where(ContextChunk.context_content_id == content_id)
    db.execute(
        update(ContextCheckpointMapping)
        .where(
            ContextCheckpointMapping.is_active == true(),
            ContextCheckpointMapping.context_chunk_id.in_(chunk_ids),
        )
        .values(is_active=False, deactivated_at=utc_now())
    )


def _clean_title(title: str) -> str:
    return title.strip()[:NOTE_TITLE_MAX_LENGTH]


def _require_project(db: Session, owner_id: int, project_id: int) -> None:
    exists = db.scalar(
        select(Project.id).where(Project.id == project_id, Project.owner_id == owner_id)
    )
    if exists is None:
        raise api_error(404, "PROJECT_NOT_FOUND", "Project not found")


def _title_from(filename: str) -> str:
    stem = PurePosixPath(basename(filename)).stem
    return (stem or "Untitled document")[:TITLE_MAX_LENGTH]