"""
Business rules for projects: create, list, get and update.

Analogy: the filing clerk at the agency. Every request says whose folder it
wants. The clerk looks only in that person's drawer. A folder that exists but
sits in someone else's drawer is reported as "not found", never as "forbidden",
so an outsider cannot even confirm that the folder exists.

Routes handle HTTP. This module handles the rules and the database, so the same
logic can be tested without starting a web server.
"""

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import Project, User
from app.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate, check_date_order


def create_project(db: Session, owner: User, payload: ProjectCreate) -> ProjectRead:
    """Save a new project for the signed-in user and return it."""
    project = Project(
        name=payload.name,
        description=payload.description,
        owner_id=owner.id,
        start_date=payload.start_date,
        end_date=payload.end_date,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return _to_read(project, owner.name)


def list_projects(db: Session, owner_id: int, limit: int) -> list[ProjectRead]:
    """The owner's most recently updated projects, newest first."""
    statement = (
        select(Project, User.name)
        .join(User, User.id == Project.owner_id)
        .where(Project.owner_id == owner_id)
        .order_by(Project.updated_at.desc(), Project.id.desc())
        .limit(limit)
    )
    return [_to_read(project, owner_name) for project, owner_name in db.execute(statement).all()]


def get_project(db: Session, owner_id: int, project_id: int) -> ProjectRead | None:
    """
    One project, only if the owner matches.

    Returns None for both "does not exist" and "belongs to someone else", so the
    caller cannot tell the two apart.
    """
    statement = (
        select(Project, User.name)
        .join(User, User.id == Project.owner_id)
        .where(Project.id == project_id, Project.owner_id == owner_id)
    )
    row = db.execute(statement).first()
    if row is None:
        return None
    project, owner_name = row
    return _to_read(project, owner_name)


def update_project(
    db: Session, owner_id: int, project_id: int, payload: ProjectUpdate
) -> ProjectRead | None:
    """
    Change the fields that were sent and stamp updated_at.

    Only fields present in the request are changed (payload.model_fields_set).
    The date check uses the merged result, so sending only an end date is still
    checked against the stored start date.
    """
    project = db.scalar(
        select(Project).where(Project.id == project_id, Project.owner_id == owner_id)
    )
    if project is None:
        return None

    sent = payload.model_fields_set
    new_start = payload.start_date if "start_date" in sent else project.start_date
    new_end = payload.end_date if "end_date" in sent else project.end_date
    # Check before changing anything, so a rejected request leaves the row untouched.
    try:
        check_date_order(new_start, new_end)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail={"code": "INVALID_DATE_RANGE", "message": str(exc)},
        ) from None

    if "name" in sent:
        project.name = payload.name
    if "description" in sent:
        project.description = payload.description
    project.start_date = new_start
    project.end_date = new_end
    project.updated_at = utc_now()

    db.commit()
    return get_project(db, owner_id, project_id)


def _to_read(project: Project, owner_name: str) -> ProjectRead:
    return ProjectRead(
        id=project.id,
        name=project.name,
        description=project.description,
        owner_id=project.owner_id,
        owner_name=owner_name,
        start_date=project.start_date,
        end_date=project.end_date,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )
