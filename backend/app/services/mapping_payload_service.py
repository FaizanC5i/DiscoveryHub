"""
Builds the request the Helper Agent receives: the active checkpoints plus one batch of chunks.

Analogy: the briefing pack handed to a reviewer. Every reviewer gets the full checklist
(all active checkpoints), but each reviewer only receives a few pages to read (the chunks
in one batch). The checklist is printed fresh from the master copy every time, so a
checkpoint switched off this morning is not on the list this afternoon.

Correctness: checkpoints are read from the database on every call and never cached in
code. Only fields the agent needs are included; the internal start_char is not sent.
"""

from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.db.models import DiscoveryCheckpoint, DiscoveryPillar

CHUNK_FIELDS = ("id", "context_content_id", "chunk_number", "chunk_text", "page_number")


def load_active_checkpoints(db: Session) -> list[dict]:
    """Every active checkpoint, with its pillar name, in pillar and sort order."""
    rows = db.execute(
        select(DiscoveryCheckpoint, DiscoveryPillar.name)
        .join(DiscoveryPillar, DiscoveryPillar.id == DiscoveryCheckpoint.pillar_id)
        .where(DiscoveryCheckpoint.is_active == true())
        .order_by(DiscoveryCheckpoint.pillar_id, DiscoveryCheckpoint.sort_order, DiscoveryCheckpoint.id)
    ).all()
    return [
        {
            "id": checkpoint.id,
            "pillar_id": checkpoint.pillar_id,
            "pillar_name": pillar_name,
            "code": checkpoint.code,
            "name": checkpoint.name,
            "description": checkpoint.description,
            "question": checkpoint.question,
            "why_it_matters": checkpoint.why_it_matters,
            "priority": checkpoint.priority,
            "readiness_required_count": checkpoint.readiness_required_count,
            "feeds_details": checkpoint.feeds_details,
            "config_json": checkpoint.config_json,
            "sort_order": checkpoint.sort_order,
            "is_active": checkpoint.is_active,
        }
        for checkpoint, pillar_name in rows
    ]


def build_mapping_request(db: Session, project_id: int, chunks: list[dict]) -> dict:
    """The body of one agent call: every active checkpoint, and only this batch's chunks."""
    return {
        "project_id": project_id,
        "discovery_checkpoints": load_active_checkpoints(db),
        "context_chunks": [{field: chunk[field] for field in CHUNK_FIELDS} for chunk in chunks],
    }
