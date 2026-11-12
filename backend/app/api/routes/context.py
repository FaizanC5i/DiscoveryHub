"""
HTTP endpoints for project documents, under /api/projects/{project_id}/sources.

Analogy: the same reception desk as the projects routes. It checks who is
asking, reads the upload, and hands it to the service. It contains no rules.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import api_error
from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.context import SourceRead
from app.services import context_service
from app.services.storage.blob_storage import BlobStorage, get_blob_storage

router = APIRouter(prefix="/api/projects/{project_id}/sources", tags=["context"])

DbSession = Annotated[Session, Depends(get_db)]
Storage = Annotated[BlobStorage, Depends(get_blob_storage)]


@router.post("", status_code=201, response_model=SourceRead)
def upload_source(
    project_id: int,
    file: Annotated[UploadFile, File()],
    user: CurrentUser,
    db: DbSession,
    storage: Storage,
) -> SourceRead:
    """
    Upload one document. Returns 201 even when text recognition fails: the
    response's processing_status is "failed" with a failure_reason, and the
    file stays in the library so it can be retried.
    """
    settings = get_settings()
    max_bytes = settings.upload_max_mb * 1024 * 1024

    # Read one byte past the limit so an oversized file is detected without loading it all.
    data = file.file.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise api_error(413, "FILE_TOO_LARGE", f"Files must be {settings.upload_max_mb} MB or smaller.")
    if not data:
        raise api_error(422, "EMPTY_FILE", "This file is empty.")

    return context_service.upload_source(db, storage, user, project_id, file.filename or "", data)


@router.get("", response_model=list[SourceRead])
def list_sources(project_id: int, user: CurrentUser, db: DbSession) -> list[SourceRead]:
    return context_service.list_sources(db, user.id, project_id)


@router.post("/{source_id}/reprocess", response_model=SourceRead)
def reprocess_source(
    project_id: int,
    source_id: int,
    user: CurrentUser,
    db: DbSession,
    storage: Storage,
) -> SourceRead:
    return context_service.reprocess_source(db, storage, user.id, project_id, source_id)


@router.delete("/{source_id}", status_code=204)
def delete_source(
    project_id: int,
    source_id: int,
    user: CurrentUser,
    db: DbSession,
    storage: Storage,
) -> Response:
    context_service.delete_source(db, storage, user.id, project_id, source_id)
    return Response(status_code=204)