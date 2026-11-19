"""
Owner decisions on the User Discovery answers: approve a proposal, and build the review cards.

Analogy: the sign-off desk. Only the project owner can sign. Signing creates a numbered version,
updates the current answer, and keeps the evidence that backed it. Old versions are never changed.
"""

import json
from collections import defaultdict

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import (
    CheckpointAnswerEvidence,
    CheckpointAnswerProposal,
    CheckpointAnswerVersion,
    ContextChunk,
    ContextContent,
    ContextSource,
    ProjectCheckpointAnswer,
    ProposalEvidence,
)
from app.services.answers.answer_pipeline import is_running
from app.services.answers.common import ReviewError, answer_summary, latest_version_number, require_owner
from app.services.answers.user_context import (
    active_user_checkpoints,
    current_answers,
    failed_mapping_count,
    pending_mapping_count,
    project_mapping_rows,
)

PROPOSAL_PENDING = "PENDING"
PROPOSAL_APPROVED = "APPROVED"
PROPOSAL_SUPERSEDED = "SUPERSEDED"
ANSWER_APPROVED = "APPROVED"


def approve_proposal(
    db: Session,
    owner_id: int,
    project_id: int,
    proposal_id: int,
    override_text: str | None = None,
) -> dict:
    require_owner(db, owner_id, project_id)

    proposal = db.scalar(
        select(CheckpointAnswerProposal)
        .join(ProjectCheckpointAnswer, ProjectCheckpointAnswer.id == CheckpointAnswerProposal.current_answer_id)
        .where(CheckpointAnswerProposal.id == proposal_id, ProjectCheckpointAnswer.project_id == project_id)
    )
    if proposal is None:
        raise ReviewError(404, "PROPOSAL_NOT_FOUND", "Proposal not found")
    if proposal.status == PROPOSAL_APPROVED:
        raise ReviewError(409, "ALREADY_APPROVED", "This proposal is already approved.")
    if proposal.status == PROPOSAL_SUPERSEDED:
        raise ReviewError(409, "PROPOSAL_SUPERSEDED", "A newer proposal replaced this one. Approve the latest proposal.")
    final_text = override_text.strip() if override_text else ""
    answer_text = final_text if final_text else proposal.proposed_answer
    source = "MANUAL" if final_text else "AI_PROPOSAL"

    if not answer_text.strip():
        raise ReviewError(409, "NO_ANSWER_TO_APPROVE", "The agent has not written an answer yet. Regenerate it.")

    answer = db.get(ProjectCheckpointAnswer, proposal.current_answer_id)
    latest = latest_version_number(db, answer.id)
    if proposal.base_version_number != latest:
        raise ReviewError(409, "STALE_PROPOSAL", "A newer answer was approved after this proposal. Regenerate it.")

    now = utc_now()
    version = CheckpointAnswerVersion(
        checkpoint_answer_id=answer.id,
        version_number=latest + 1,
        answer_text=answer_text,
        source=source,
        proposal_id=proposal.id,
        created_by=owner_id,
        created_at=now,
    )
    db.add(version)
    db.flush()

    answer.current_answer = answer_text
    answer.status = ANSWER_APPROVED
    answer.is_completed = proposal.is_completed
    answer.completion_score = proposal.completion_score
    answer.completion_updated_by_run_id = proposal.agent_run_id
    answer.completion_updated_at = now
    answer.approved_by = owner_id
    answer.approved_at = now
    answer.updated_at = now

    links = db.scalars(select(ProposalEvidence).where(ProposalEvidence.proposal_id == proposal.id)).all()
    for link in links:
        db.add(CheckpointAnswerEvidence(
            checkpoint_answer_id=answer.id,
            answer_version_id=version.id,
            context_chunk_id=link.context_chunk_id,
        ))

    proposal.status = PROPOSAL_APPROVED
    proposal.reviewed_at = now
    db.commit()
    return {"proposal_id": proposal.id, "checkpoint_answer_id": answer.id, "version_number": version.version_number}


def build_overview(db: Session, project_id: int) -> dict:
    defs = sorted(active_user_checkpoints(db).values(), key=lambda cp: (cp.sort_order, cp.id))
    evidence: dict[int, dict[int, dict]] = defaultdict(dict)
    for row in project_mapping_rows(db, project_id):
        evidence[row["checkpoint_id"]].setdefault(row["chunk_id"], {
            "chunk_id": row["chunk_id"],
            "source_title": row["source_title"],
            "page_number": row["page_number"],
            "chunk_text": row["chunk_text"],
        })

    answers = current_answers(db, project_id, {cp.id for cp in defs})
    pending = _pending_proposals(db, project_id)

    cards = []
    for cp in defs:
        items = list(evidence.get(cp.id, {}).values())
        proposal = pending.get(cp.id)
        cards.append({
            "checkpoint": {"id": cp.id, "code": cp.code, "name": cp.name, "question": cp.question},
            "current_answer": answer_summary(answers.get(cp.id)),
            "owner_input": answers[cp.id].owner_input if cp.id in answers else None,
            "chunk_count": len(items),
            "evidence": items,
            "pending_proposal": _proposal_view(db, proposal) if proposal else None,
        })

    return {
        "running": is_running(project_id),
        "pending_mapping_chunks": pending_mapping_count(db, project_id),
        "failed_mapping_chunks": failed_mapping_count(db, project_id),
        "checkpoints": cards,
    }


def _pending_proposals(db: Session, project_id: int) -> dict[int, CheckpointAnswerProposal]:
    rows = db.execute(
        select(CheckpointAnswerProposal, ProjectCheckpointAnswer.checkpoint_id)
        .join(ProjectCheckpointAnswer, ProjectCheckpointAnswer.id == CheckpointAnswerProposal.current_answer_id)
        .where(
            ProjectCheckpointAnswer.project_id == project_id,
            CheckpointAnswerProposal.status == PROPOSAL_PENDING,
        )
        .order_by(CheckpointAnswerProposal.id)
    ).all()
    return {checkpoint_id: proposal for proposal, checkpoint_id in rows}


def _proposal_view(db: Session, proposal: CheckpointAnswerProposal) -> dict:
    rows = db.execute(
        select(
            ProposalEvidence.reason,
            ContextChunk.id,
            ContextChunk.page_number,
            ContextChunk.chunk_text,
            func.coalesce(ContextSource.original_filename, ContextSource.title),
        )
        .join(ContextChunk, ContextChunk.id == ProposalEvidence.context_chunk_id)
        .join(ContextContent, ContextContent.id == ContextChunk.context_content_id)
        .join(ContextSource, ContextSource.id == ContextContent.context_source_id)
        .where(ProposalEvidence.proposal_id == proposal.id)
        .order_by(ContextChunk.id)
    ).all()

    return {
        "id": proposal.id,
        "proposed_answer": proposal.proposed_answer,
        "agent_status": proposal.agent_status,
        "is_completed": proposal.is_completed,
        "completion_score": float(proposal.completion_score) if proposal.completion_score is not None else None,
        "base_version_number": proposal.base_version_number,
        "created_at": proposal.created_at.isoformat() if proposal.created_at else None,
        "missing_information": json.loads(proposal.missing_information or "[]"),
        "clarification_questions": json.loads(proposal.clarification_questions or "[]"),
        "evidence": [
            {
                "chunk_id": chunk_id,
                "source_title": title,
                "page_number": page,
                "chunk_text": text,
                "reason": reason,
            }
            for reason, chunk_id, page, text, title in rows
        ],
    }