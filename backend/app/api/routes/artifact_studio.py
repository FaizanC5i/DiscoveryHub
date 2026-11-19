"""
Artifact Studio endpoints, at the paths written in frontend/features/artifact-studio/services/
artifact-studio.service.ts, returning the shapes in artifact-studio.types.ts.

Generate, Regenerate and Clarify run the agent in the background: they answer 202 with an
agent_run_id, and GET .../artifacts/{code} shows status "Generating" until the run ends.
"""

from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Path, Query, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.dependencies.auth import CurrentUser
from app.services import artifact_studio_service as studio
from app.services import brd_service

router = APIRouter(prefix="/api/projects/{project_id}", tags=["artifact-studio"])

DbSession = Annotated[Session, Depends(get_db)]
Code = Annotated[str, Path(max_length=40, pattern=r"^[A-Za-z_]+$")]
SectionId = Annotated[str, Path(max_length=50, pattern=r"^[a-z_]+$")]


class DraftConfig(BaseModel):
    title: str = Field(default="", max_length=255)
    audience: str = Field(default="", max_length=100)
    scope: str = Field(default="", max_length=1000)


class SectionEdit(BaseModel):
    """Either the section's Markdown text (content) or a list of points (bullets)."""

    content: str | None = Field(default=None, max_length=100000)
    bullets: list[str] | None = Field(default=None, max_length=200)


class ClarificationAnswer(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    answer: str = Field(max_length=20000)


class RegenerateBody(BaseModel):
    answers: list[ClarificationAnswer] = Field(default_factory=list, max_length=10)


@router.get("/artifact-studio")
def studio_page(project_id: int, user: CurrentUser, db: DbSession) -> dict:
    return studio.studio_data(db, user.id, project_id)


@router.post("/artifacts/{code}/generate", status_code=status.HTTP_202_ACCEPTED)
def generate(project_id: int, code: Code, body: DraftConfig, background: BackgroundTasks, user: CurrentUser, db: DbSession) -> dict:
    run_id = studio.generate(db, user.id, project_id, code, body.model_dump())
    background.add_task(brd_service.run_brd_job, run_id)
    return {"agentRunId": run_id}


@router.get("/artifacts/{code}")
def draft(project_id: int, code: Code, user: CurrentUser, db: DbSession) -> dict:
    return studio.draft(db, user.id, project_id, code)


@router.put("/artifacts/{code}/sections/{section_id}")
def save_section(project_id: int, code: Code, section_id: SectionId, body: SectionEdit, user: CurrentUser, db: DbSession) -> dict:
    return studio.save_section(db, user.id, project_id, code, section_id, bullets=body.bullets, content=body.content)


@router.post("/artifacts/{code}/sections/{section_id}/regenerate", status_code=status.HTTP_202_ACCEPTED)
def regenerate_section(
    project_id: int,
    code: Code,
    section_id: SectionId,
    background: BackgroundTasks,
    user: CurrentUser,
    db: DbSession,
    body: RegenerateBody | None = None,
) -> dict:
    answers = [a.model_dump() for a in body.answers] if body else []
    run_id = studio.regenerate_section(db, user.id, project_id, code, section_id, answers)
    background.add_task(brd_service.run_brd_job, run_id)
    return {"agentRunId": run_id}


@router.post("/artifacts/{code}/sections/{section_id}/clarify", status_code=status.HTTP_202_ACCEPTED)
def clarify_section(project_id: int, code: Code, section_id: SectionId, background: BackgroundTasks, user: CurrentUser, db: DbSession) -> dict:
    run_id = studio.clarify_section(db, user.id, project_id, code, section_id)
    background.add_task(brd_service.run_brd_job, run_id)
    return {"agentRunId": run_id}


@router.post("/artifacts/{code}/versions")
def save_version(project_id: int, code: Code, user: CurrentUser, db: DbSession) -> dict:
    return studio.save_version(db, user.id, project_id, code)


@router.get("/artifacts/{code}/export")
def export(
    project_id: int,
    code: Code,
    user: CurrentUser,
    db: DbSession,
    format: Annotated[str, Query(pattern=r"^(md|docx|pdf)$")] = "md",
    sources: bool = True,
    questions: bool = True,
) -> Response:
    file_name, media_type, content = studio.export(db, user.id, project_id, code, format, sources, questions)
    return Response(content, media_type=media_type, headers={"Content-Disposition": f'attachment; filename="{file_name}"'})
