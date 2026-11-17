"""
Shared pieces for the answer feature: the error every route uses, the owner check, and the
summary of a current answer.

Analogy: one rubber stamp for every desk, so a refusal always looks the same.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import CheckpointAnswerVersion, Project, ProjectCheckpointAnswer


class ReviewError(Exception):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message


def require_owner(db: Session, owner_id: int, project_id: int) -> None:
    found = db.scalar(select(Project.id).where(Project.id == project_id, Project.owner_id == owner_id))
    if found is None:
        raise ReviewError(404, "PROJECT_NOT_FOUND", "Project not found")


def latest_version_number(db: Session, answer_id: int) -> int:
    return db.scalar(
        select(func.coalesce(func.max(CheckpointAnswerVersion.version_number), 0))
        .where(CheckpointAnswerVersion.checkpoint_answer_id == answer_id)
    ) or 0


def answer_summary(answer: ProjectCheckpointAnswer | None) -> dict | None:
    if answer is None or not answer.current_answer:
        return None
    return {
        "text": answer.current_answer,
        "status": answer.status,
        "is_completed": answer.is_completed,
        "completion_score": float(answer.completion_score) if answer.completion_score is not None else None,
        "approved_at": answer.approved_at.isoformat() if answer.approved_at else None,
    }