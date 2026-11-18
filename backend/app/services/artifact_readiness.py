"""
How ready a project's discovery is for an artifact: per checkpoint, verified / awaiting review / missing.

Analogy: the checklist pinned next to the printer. Before printing a document you count how many
of its required facts are signed off, how many are still on someone's desk, and how many nobody
has written yet. Only signed-off facts go into the document.

- verified: the answer is approved (approved_at is set and the answer is not empty)
- review:   not verified, but the agent has a PENDING proposal waiting for the owner
- missing:  neither
"""

from sqlalchemy import func, select, true
from sqlalchemy.orm import Session

from app.db.models import (
    CheckpointAnswerProposal,
    ContextSource,
    DiscoveryCheckpoint,
    DiscoveryPillar,
    ProjectCheckpointAnswer,
)


def checkpoint_states(db: Session, project_id: int, pillar_ids: set[int] | None) -> list[dict]:
    """One row per active checkpoint of the pillars (all pillars when None), with its state."""
    query = (
        select(DiscoveryCheckpoint.id, DiscoveryCheckpoint.code, DiscoveryPillar.id, DiscoveryPillar.code, DiscoveryPillar.name)
        .join(DiscoveryPillar, DiscoveryPillar.id == DiscoveryCheckpoint.pillar_id)
        .where(DiscoveryCheckpoint.is_active == true())
        .order_by(DiscoveryPillar.id, DiscoveryCheckpoint.sort_order)
    )
    if pillar_ids is not None:
        query = query.where(DiscoveryCheckpoint.pillar_id.in_(pillar_ids))
    checkpoints = db.execute(query).all()

    answers = {
        checkpoint_id: (approved_at, text)
        for checkpoint_id, approved_at, text in db.execute(
            select(
                ProjectCheckpointAnswer.checkpoint_id,
                ProjectCheckpointAnswer.approved_at,
                ProjectCheckpointAnswer.current_answer,
            ).where(ProjectCheckpointAnswer.project_id == project_id)
        ).all()
    }
    pending = set(
        db.scalars(
            select(ProjectCheckpointAnswer.checkpoint_id)
            .join(CheckpointAnswerProposal, CheckpointAnswerProposal.current_answer_id == ProjectCheckpointAnswer.id)
            .where(ProjectCheckpointAnswer.project_id == project_id, CheckpointAnswerProposal.status == "PENDING")
        )
    )

    rows = []
    for checkpoint_id, code, pillar_id, pillar_code, pillar_name in checkpoints:
        approved_at, text = answers.get(checkpoint_id, (None, None))
        if approved_at is not None and (text or "").strip():
            state = "verified"
        elif checkpoint_id in pending:
            state = "review"
        else:
            state = "missing"
        rows.append({
            "checkpoint_id": checkpoint_id, "code": code, "state": state,
            "pillar_id": pillar_id, "pillar_code": pillar_code, "pillar_name": pillar_name,
        })
    return rows


def readiness(db: Session, project_id: int, pillar_ids: set[int] | None) -> dict:
    """The "Review evidence readiness" card: totals, percent, and one row per pillar."""
    rows = checkpoint_states(db, project_id, pillar_ids)
    total = len(rows)
    verified = sum(r["state"] == "verified" for r in rows)
    review = sum(r["state"] == "review" for r in rows)

    pillars: dict[int, dict] = {}
    for r in rows:
        p = pillars.setdefault(r["pillar_id"], {
            "pillarId": r["pillar_code"],
            "label": _pillar_label(r["pillar_name"]),
            "verified": 0, "total": 0, "missing": 0, "review": 0,
        })
        p["total"] += 1
        p[r["state"]] += 1
    for p in pillars.values():
        if p["verified"] == p["total"]:
            p["status"] = "Complete"
        elif p["verified"] or p["review"]:
            p["status"] = "In progress"
        else:
            p["status"] = "Not started"

    return {
        "percent": round(verified * 100 / total) if total else 0,
        "verified": verified,
        "awaitingReview": review,
        "withoutEvidence": total - verified - review,
        "total": total,
        "pillars": list(pillars.values()),
    }


def source_count(db: Session, project_id: int) -> int:
    return db.scalar(
        select(func.count()).select_from(ContextSource).where(
            ContextSource.project_id == project_id, ContextSource.deleted_at.is_(None)
        )
    ) or 0


def snapshot(db: Session, project_id: int, pillar_ids: set[int] | None) -> dict:
    """The draft banner: "x/y verified items from n sources; m missing; k unreviewed answers excluded"."""
    ready = readiness(db, project_id, pillar_ids)
    return {
        "verified": ready["verified"],
        "total": ready["total"],
        "sources": source_count(db, project_id),
        "missing": ready["withoutEvidence"],
        "unreviewedExcluded": ready["awaitingReview"],
    }


def _pillar_label(name: str) -> str:
    """'User Discovery' -> 'User'."""
    return name.removesuffix(" Discovery").strip() or name
