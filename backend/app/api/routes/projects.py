"""
HTTP endpoints for projects, mounted under /api/projects.

Analogy: the reception desk for the filing room. Every route first asks the
door security (CurrentUser) who is asking, then passes the request to the clerk
(services/project_service.py). The desk adds no rules of its own.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from app.services import project_service

router = APIRouter(prefix="/api/projects", tags=["projects"])

DbSession = Annotated[Session, Depends(get_db)]

# How many projects the dashboard may ask for in one call. Keeps one request from loading everything.
MAX_LIST_LIMIT = 50


def _not_found() -> HTTPException:
    # Same answer for "missing" and "belongs to someone else", so the response reveals nothing about other users.
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "PROJECT_NOT_FOUND", "message": "Project not found"},
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProjectRead)
def create_project(payload: ProjectCreate, user: CurrentUser, db: DbSession) -> ProjectRead:
    """Create a project owned by the signed-in user."""
    return project_service.create_project(db, user, payload)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    user: CurrentUser,
    db: DbSession,
    limit: Annotated[int, Query(ge=1, le=MAX_LIST_LIMIT)] = 5,
) -> list[ProjectRead]:
    """The signed-in user's projects, most recently updated first."""
    return project_service.list_projects(db, user.id, limit)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, user: CurrentUser, db: DbSession) -> ProjectRead:
    """One project. 404 when it is missing or owned by someone else."""
    project = project_service.get_project(db, user.id, project_id)
    if project is None:
        raise _not_found()
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    payload: ProjectUpdate,
    user: CurrentUser,
    db: DbSession,
) -> ProjectRead:
    """Change the fields that were sent. Sets updated_at."""
    project = project_service.update_project(db, user.id, project_id, payload)
    if project is None:
        raise _not_found()
    return project
