"""
HTTP endpoints for BRD generation. The agent calls run in the background: the POST endpoints
return 202 with an agent_run_id, and the client polls GET .../brd (latest_run) or .../brd/runs/{id}.

Analogy: the same reception desk as the other routes. It checks who is calling, passes the
request to brd_service, and adds no rules of its own.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.schemas.brd import (
    BrdApproved,
    BrdRead,
    BrdRun,
    BrdRunQueued,
    BrdSection,
    BrdVersion,
    BrdVersionSummary,
    RegenerateRequest,
    SectionEdit,
)
from app.services import brd_service

router = APIRouter(prefix="/api/projects/{project_id}/brd", tags=["brd"])

DbSession = Annotated[Session, Depends(get_db)]
SectionKey = Annotated[str, Path(max_length=50, pattern=r"^[a-z_]+$")]


@router.get("", response_model=BrdRead)
def read_brd(project_id: int, user: CurrentUser, db: DbSession) -> dict:
    return brd_service.get_brd(db, user.id, project_id)


@router.post("/generate", status_code=status.HTTP_202_ACCEPTED, response_model=BrdRunQueued)
def generate_brd(project_id: int, background: BackgroundTasks, user: CurrentUser, db: DbSession) -> dict:
    """Write all 14 sections from the project's approved checkpoint answers."""
    run_id = brd_service.start_generate(db, user.id, project_id)
    background.add_task(brd_service.run_brd_job, run_id)
    return {"agent_run_id": run_id}


@router.post(
    "/sections/{section_key}/regenerate", status_code=status.HTTP_202_ACCEPTED, response_model=BrdRunQueued
)
def regenerate_section(
    project_id: int,
    section_key: SectionKey,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
    body: RegenerateRequest | None = None,
) -> dict:
    """Rewrite one section. Send answers to its clarification questions to have them saved and used."""
    answers = [a.model_dump() for a in body.answers] if body else []
    run_id = brd_service.start_regenerate(db, user.id, project_id, section_key, answers)
    background.add_task(brd_service.run_brd_job, run_id)
    return {"agent_run_id": run_id}


@router.post("/sections/{section_key}/clarify", status_code=status.HTTP_202_ACCEPTED, response_model=BrdRunQueued)
def clarify_section(
    project_id: int, section_key: SectionKey, background: BackgroundTasks, user: CurrentUser, db: DbSession
) -> dict:
    """Ask the agent for up to 3 questions about one section."""
    run_id = brd_service.start_clarify(db, user.id, project_id, section_key)
    background.add_task(brd_service.run_brd_job, run_id)
    return {"agent_run_id": run_id}


@router.put("/sections/{section_key}", response_model=BrdSection)
def edit_section(project_id: int, section_key: SectionKey, body: SectionEdit, user: CurrentUser, db: DbSession) -> dict:
    """The user's own text becomes the section's approved content."""
    return brd_service.edit_section(db, user.id, project_id, section_key, body.content)


@router.post("/proposals/{proposal_id}/approve", response_model=BrdSection)
def approve_proposal(project_id: int, proposal_id: int, user: CurrentUser, db: DbSession) -> dict:
    return brd_service.approve_proposal(db, user.id, project_id, proposal_id)


@router.post("/proposals/{proposal_id}/reject", response_model=BrdSection)
def reject_proposal(project_id: int, proposal_id: int, user: CurrentUser, db: DbSession) -> dict:
    return brd_service.reject_proposal(db, user.id, project_id, proposal_id)


@router.post("/approve", response_model=BrdApproved)
def approve_brd(project_id: int, user: CurrentUser, db: DbSession) -> dict:
    """Freeze the current section contents as the next BRD version."""
    return brd_service.approve_brd(db, user.id, project_id)


@router.get("/versions", response_model=list[BrdVersionSummary])
def list_versions(project_id: int, user: CurrentUser, db: DbSession) -> list[dict]:
    return brd_service.list_versions(db, user.id, project_id)


@router.get("/versions/{version_number}", response_model=BrdVersion)
def read_version(project_id: int, version_number: int, user: CurrentUser, db: DbSession) -> dict:
    return brd_service.get_version(db, user.id, project_id, version_number)


@router.get("/runs/{agent_run_id}", response_model=BrdRun)
def read_run(project_id: int, agent_run_id: int, user: CurrentUser, db: DbSession) -> dict:
    return brd_service.get_run(db, user.id, project_id, agent_run_id)
