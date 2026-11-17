"""
HTTP endpoints for manual notes, under /api/projects/{project_id}/notes.

A note is a context source with source_type MANUAL_NOTE. Listing, retry, and removal
use the source endpoints in context.py, so notes appear beside files without a second list.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.api.routes.context import queue_source_mapping, read_sources
from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.context import NoteInput, NoteRead, SourceRead
from app.services import context_service

router = APIRouter(prefix="/api/projects/{project_id}/notes", tags=["context"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", status_code=201, response_model=SourceRead)
def create_note(
    project_id: int,
    payload: NoteInput,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
) -> SourceRead:
    source = context_service.create_note(db, user, project_id, payload.title, payload.body)
    queue_source_mapping(background, db, source)
    return read_sources(db, [source])[0]


@router.get("/{source_id}", response_model=NoteRead)
def get_note(project_id: int, source_id: int, user: CurrentUser, db: DbSession) -> NoteRead:
    details = context_service.get_note(db, user.id, project_id, source_id)
    return NoteRead(
        id=details.source.id,
        project_id=details.source.project_id,
        title=details.source.title,
        body=details.content.content_text,
        processing_status=details.source.processing_status,
        failure_reason=details.source.failure_reason,
        chunk_count=details.chunk_count,
        created_by_name=details.created_by_name,
        created_at=details.source.created_at,
        updated_at=details.source.updated_at,
    )


@router.patch("/{source_id}", response_model=SourceRead)
def update_note(
    project_id: int,
    source_id: int,
    payload: NoteInput,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
) -> SourceRead:
    source = context_service.update_note(
        db, user.id, project_id, source_id, payload.title, payload.body
    )
    queue_source_mapping(background, db, source)
    return read_sources(db, [source])[0]
