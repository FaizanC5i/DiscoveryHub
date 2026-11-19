"""
HTTP endpoints for checkpoint mappings.

Analogy: the same reception desk as the other routes. It asks who is calling, then passes
the request to the service. It adds no rules of its own.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.mapping import MappingRead, MappingRetryQueued
from app.services import chunk_mapping_service, mapping_query_service

router = APIRouter(tags=["mappings"])

DbSession = Annotated[Session, Depends(get_db)]


@router.get("/api/context-content/{content_id}/mappings", response_model=list[MappingRead])
def list_content_mappings(content_id: int, user: CurrentUser, db: DbSession) -> list[dict]:
    return mapping_query_service.list_content_mappings(db, user.id, content_id)


@router.get("/api/projects/{project_id}/mappings", response_model=list[MappingRead])
def list_project_mappings(
    project_id: int,
    user: CurrentUser,
    db: DbSession,
    checkpoint_code: Annotated[str | None, Query(max_length=20)] = None,
) -> list[dict]:
    return mapping_query_service.list_project_mappings(db, user.id, project_id, checkpoint_code)


@router.post(
    "/api/context-content/{content_id}/chunks/map",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=MappingRetryQueued,
)
def retry_mapping(content_id: int, background: BackgroundTasks, user: CurrentUser, db: DbSession) -> dict:
    """Queue mapping again for this document's chunks that are FAILED or PENDING."""
    owned_content_id = mapping_query_service.retryable_content(db, user.id, content_id)
    chunk_ids = chunk_mapping_service.retry_chunk_ids(db, owned_content_id)
    chunk_mapping_service.enqueue_chunk_mapping(background, chunk_ids)
    return {"queued": len(chunk_ids)}
