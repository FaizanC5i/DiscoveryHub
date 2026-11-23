"""
Builds the User Discovery agent's request from the database.

Analogy: the case file clerk. The sorting office (pillar_dispatch_service) groups mapped chunks
by pillar. This clerk takes the User Discovery pile and adds what the specialist needs: the full
checkpoint definition and the current answer. The result matches AGENT_IO_LOG.md, section 1.2.
"""

import json
from dataclasses import dataclass

from sqlalchemy import func, select, true
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import (
    Agent,
    ContextCheckpointMapping,
    ContextChunk,
    ContextContent,
    ContextSource,
    DiscoveryCheckpoint,
    DiscoveryPillar,
    MappingEvidence,
    ProjectCheckpointAnswer,
)
from app.services.answers.common import answer_summary
from app.services.answers.user_agent import SentCheckpoint
from collections import defaultdict
USER_PILLAR_CODE = "USER"
DB_AGENT_CODE = "USER_AGENT"
PROMPT_AGENT_CODE = "USER_DISCOVERY_AGENT"
PROMPT_PILLAR_CODE = "USER_DISCOVERY"
PENDING_MAPPING_STATUSES = ("PENDING", "IN_PROGRESS")

DEFINITION_FIELDS = (
    "id", "code", "name", "description", "question", "why_it_matters", "priority",
    "readiness_required_count", "feeds_details", "sort_order", "is_active",
)


@dataclass
class AgentBatch:
    payload: dict
    sent: list[SentCheckpoint]
    chunk_count: int


def active_user_checkpoints(db: Session) -> dict[int, DiscoveryCheckpoint]:
    rows = db.scalars(
        select(DiscoveryCheckpoint)
        .join(DiscoveryPillar, DiscoveryPillar.id == DiscoveryCheckpoint.pillar_id)
        .where(DiscoveryPillar.code == USER_PILLAR_CODE, DiscoveryCheckpoint.is_active == true())
    ).all()
    return {row.id: row for row in rows}


def project_mapping_rows(db: Session, project_id: int, checkpoint_ids: list[int] | None = None) -> list[dict]:
    """Active User mappings of the project, one row per evidence item, on documents not removed."""
    statement = (
        select(
            ContextCheckpointMapping.id.label("mapping_id"),
            DiscoveryCheckpoint.id.label("checkpoint_id"),
            DiscoveryCheckpoint.code.label("checkpoint_code"),
            DiscoveryCheckpoint.name.label("checkpoint_name"),
            DiscoveryCheckpoint.question.label("question"),
            DiscoveryCheckpoint.why_it_matters.label("why_it_matters"),
            DiscoveryCheckpoint.sort_order.label("sort_order"),
            DiscoveryPillar.id.label("pillar_id"),
            DiscoveryPillar.code.label("pillar_code"),
            DiscoveryPillar.name.label("pillar_name"),
            ContextChunk.id.label("chunk_id"),
            ContextChunk.chunk_number.label("chunk_number"),
            ContextChunk.chunk_text.label("chunk_text"),
            ContextChunk.page_number.label("page_number"),
            ContextSource.id.label("source_id"),
            func.coalesce(ContextSource.original_filename, ContextSource.title).label("source_title"),
            MappingEvidence.evidence_quote.label("evidence_quote"),
            MappingEvidence.reason.label("evidence_reason"),
            MappingEvidence.evidence_start_char.label("evidence_start_char"),
            MappingEvidence.evidence_end_char.label("evidence_end_char"),
        )
        .join(DiscoveryCheckpoint, DiscoveryCheckpoint.id == ContextCheckpointMapping.checkpoint_id)
        .join(DiscoveryPillar, DiscoveryPillar.id == DiscoveryCheckpoint.pillar_id)
        .join(ContextChunk, ContextChunk.id == ContextCheckpointMapping.context_chunk_id)
        .join(ContextContent, ContextContent.id == ContextChunk.context_content_id)
        .join(ContextSource, ContextSource.id == ContextContent.context_source_id)
        .outerjoin(MappingEvidence, MappingEvidence.mapping_id == ContextCheckpointMapping.id)
        .where(
            ContextCheckpointMapping.project_id == project_id,
            ContextCheckpointMapping.is_active == true(),
            ContextSource.deleted_at.is_(None),
            DiscoveryPillar.code == USER_PILLAR_CODE,
            DiscoveryCheckpoint.is_active == true(),
        )
        .order_by(ContextSource.id, ContextChunk.chunk_number, ContextCheckpointMapping.id, MappingEvidence.id)
    )
    if checkpoint_ids is not None:
        statement = statement.where(ContextCheckpointMapping.checkpoint_id.in_(checkpoint_ids))
    return [dict(row) for row in db.execute(statement).mappings().all()]


def pillar_agents(db: Session) -> dict[int, dict]:
    rows = db.execute(
        select(Agent.pillar_id, Agent.id, Agent.agent_code).where(Agent.pillar_id.is_not(None))
    ).all()
    return {pillar_id: {"agent_id": agent_id, "agent_code": code} for pillar_id, agent_id, code in rows}


def current_answers(db: Session, project_id: int, checkpoint_ids: set[int]) -> dict[int, ProjectCheckpointAnswer]:
    if not checkpoint_ids:
        return {}
    rows = db.scalars(
        select(ProjectCheckpointAnswer).where(
            ProjectCheckpointAnswer.project_id == project_id,
            ProjectCheckpointAnswer.checkpoint_id.in_(checkpoint_ids),
        )
    ).all()
    return {row.checkpoint_id: row for row in rows}


def pending_mapping_count(db: Session, project_id: int) -> int:
    return _chunk_count(db, project_id, PENDING_MAPPING_STATUSES)


def failed_mapping_count(db: Session, project_id: int) -> int:
    return _chunk_count(db, project_id, ("FAILED",))


def _chunk_count(db: Session, project_id: int, statuses: tuple[str, ...]) -> int:
    return db.scalar(
        select(func.count(ContextChunk.id))
        .join(ContextContent, ContextContent.id == ContextChunk.context_content_id)
        .join(ContextSource, ContextSource.id == ContextContent.context_source_id)
        .where(
            ContextSource.project_id == project_id,
            ContextSource.deleted_at.is_(None),
            ContextChunk.mapping_status.in_(statuses),
        )
    ) or 0


def build_agent_batch(
    db: Session,
    project_id: int,
    checkpoint_ids: list[int] | None = None,
    chunk_ids: set[int] | None = None,
) -> AgentBatch | None:
    """
    One request for every active User checkpoint. Checkpoints with no mapped chunks are still
    sent, with an empty chunk list, so the agent can report what is missing.
    checkpoint_ids limits the request, for example to one checkpoint when regenerating.
    """
    definitions = sorted(active_user_checkpoints(db).values(), key=lambda cp: (cp.sort_order, cp.id))
    if checkpoint_ids is not None:
        definitions = [cp for cp in definitions if cp.id in checkpoint_ids]

    evidence: dict[int, dict[int, dict]] = defaultdict(dict)
    for row in project_mapping_rows(db, project_id):
        if chunk_ids is None or row["chunk_id"] in chunk_ids:
            evidence[row["checkpoint_id"]].setdefault(row["chunk_id"], row)

    if chunk_ids is not None:
        definitions = [cp for cp in definitions if cp.id in evidence]
    if not definitions:
        return None

    answers = current_answers(db, project_id, {cp.id for cp in definitions})

    entries: list[dict] = []
    sent: list[SentCheckpoint] = []
    all_chunks: set[int] = set()
    for definition in definitions:
        items = list(evidence.get(definition.id, {}).values())
        all_chunks.update(item["chunk_id"] for item in items)
        entries.append({
            "checkpoint": {
                **{name: getattr(definition, name) for name in DEFINITION_FIELDS},
                "config_json": json.loads(definition.config_json or "{}"),
            },
            "chunk_ids": [str(item["chunk_id"]) for item in items],
            "evidence": [
                {
                    "chunk_id": item["chunk_id"],
                    "source_title": item["source_title"],
                    "page_number": item["page_number"],
                    "chunk_text": item["chunk_text"],
                }
                for item in items
            ],
            "current_answer": answer_summary(answers.get(definition.id)),
            "owner_input": answers[definition.id].owner_input if definition.id in answers else None,
        })
        sent.append(SentCheckpoint(
            id=definition.id,
            code=definition.code,
            chunk_ids=frozenset(item["chunk_id"] for item in items),
            mapping_by_chunk={item["chunk_id"]: item["mapping_id"] for item in items},
        ))

    payload = {
        "project_id": project_id,
        "run_id": None,
        "agent": {"agent_code": PROMPT_AGENT_CODE, "pillar_code": PROMPT_PILLAR_CODE},
        "checkpoints": entries,
    }
    return AgentBatch(payload=payload, sent=sent, chunk_count=len(all_chunks))