"""
HTTP endpoints for the chunks of one extracted text, under /api/context-content/{content_id}/chunks.

Analogy: the same reception desk as the other routes. It checks who is asking and
hands the request to the service. It contains no rules.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.context_chunk import ChunkRead
from app.services import context_chunk_service

router = APIRouter(prefix="/api/context-content/{content_id}/chunks", tags=["context"])

DbSession = Annotated[Session, Depends(get_db)]


@router.post("", response_model=list[ChunkRead])
def create_chunks(
    content_id: int,
    response: Response,
    user: CurrentUser,
    db: DbSession,
) -> list[ChunkRead]:
    """
    Split the document text into chunks. Returns 201 when chunks were created and
    200 with the existing chunks when they were already there.
    """
    result = context_chunk_service.create_chunks_for_content(db, content_id, user.id)
    response.status_code = 201 if result.created else 200
    return [ChunkRead.model_validate(chunk) for chunk in result.chunks]


@router.get("", response_model=list[ChunkRead])
def list_chunks(content_id: int, user: CurrentUser, db: DbSession) -> list[ChunkRead]:
    chunks = context_chunk_service.list_chunks(db, user.id, content_id)
    return [ChunkRead.model_validate(chunk) for chunk in chunks]
