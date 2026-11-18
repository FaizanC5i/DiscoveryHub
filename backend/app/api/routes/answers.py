"""
User Discovery endpoints. Every route checks ownership first. Other users get 404.
"""

from typing import Annotated, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.services import brd_service
from app.services.answers import answer_review
from app.services.answers.answer_pipeline import request_run, run_in_background
from app.services.answers.common import ReviewError, require_owner

router = APIRouter(prefix="/api/projects/{project_id}/user-discovery", tags=["user-discovery"])


class ApproveBody(BaseModel):
    override_text: Optional[str] = None

DbSession = Annotated[Session, Depends(get_db)]


def _refuse(exc: ReviewError):
    return api_error(exc.status_code, exc.code, exc.message)


def _start(db: Session, owner_id: int, project_id: int, checkpoint_ids, background: BackgroundTasks) -> dict:
    try:
        request_run(db, owner_id, project_id, checkpoint_ids)
    except ReviewError as exc:
        raise _refuse(exc) from None
    background.add_task(run_in_background, project_id, checkpoint_ids)
    return {"status": "started"}


@router.get("")
def overview(project_id: int, user: CurrentUser, db: DbSession) -> dict:
    try:
        require_owner(db, user.id, project_id)
    except ReviewError as exc:
        raise _refuse(exc) from None
    return answer_review.build_overview(db, project_id)


@router.post("/runs", status_code=202)
def start_run(project_id: int, background: BackgroundTasks, user: CurrentUser, db: DbSession) -> dict:
    return _start(db, user.id, project_id, None, background)


@router.post("/checkpoints/{checkpoint_id}/regenerate", status_code=202)
def regenerate(
    project_id: int,
    checkpoint_id: int,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
) -> dict:
    return _start(db, user.id, project_id, [checkpoint_id], background)


@router.post("/proposals/{proposal_id}/approve")
def approve(
    project_id: int,
    proposal_id: int,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
    body: Annotated[ApproveBody, Body()] = ApproveBody(),
) -> dict:
    try:
        result = answer_review.approve_proposal(
            db, user.id, project_id, proposal_id,
            override_text=body.override_text,
        )
    except ReviewError as exc:
        raise _refuse(exc) from None
    # A new approved answer: rewrite the BRD in the background (its output arrives as proposals).
    background.add_task(brd_service.refresh_brd, project_id)
    return result