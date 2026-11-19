"""
Reads saved mappings for the caller's own documents and projects.

Analogy: the index at the back of the filing cabinet. It lists each tag with the card it
points to and the sentence that justified it, but it never lets you open a drawer that is
not yours. Missing and foreign records give the same 404, as everywhere else.
"""

from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.core.errors import api_error
from app.db.models import (
    ContextChunk,
    ContextCheckpointMapping,
    DiscoveryCheckpoint,
    DiscoveryPillar,
    MappingEvidence,
    Project,
)
from app.services.context_chunk_service import load_owned_content


def list_content_mappings(db: Session, owner_id: int, content_id: int) -> list[dict]:
    load_owned_content(db, content_id, owner_id)
    return _mapping_rows(db, [ContextChunk.context_content_id == content_id])


def list_project_mappings(
    db: Session,
    owner_id: int,
    project_id: int,
    checkpoint_code: str | None,
) -> list[dict]:
    owned = db.scalar(select(Project.id).where(Project.id == project_id, Project.owner_id == owner_id))
    if owned is None:
        raise api_error(404, "PROJECT_NOT_FOUND", "Project not found")
    filters = [ContextCheckpointMapping.project_id == project_id]
    if checkpoint_code:
        filters.append(DiscoveryCheckpoint.code == checkpoint_code)
    return _mapping_rows(db, filters)


def retryable_content(db: Session, owner_id: int, content_id: int) -> int:
    """Confirm the content belongs to the caller and return its id."""
    content, _ = load_owned_content(db, content_id, owner_id)
    return content.id


def _mapping_rows(db: Session, filters: list) -> list[dict]:
    rows = db.execute(
        select(
            ContextCheckpointMapping.id,
            ContextCheckpointMapping.project_id,
            ContextCheckpointMapping.context_chunk_id,
            ContextChunk.context_content_id,
            ContextChunk.chunk_number,
            DiscoveryCheckpoint.id,
            DiscoveryCheckpoint.code,
            DiscoveryCheckpoint.name,
            DiscoveryPillar.name,
            MappingEvidence.evidence_quote,
            MappingEvidence.evidence_start_char,
            MappingEvidence.evidence_end_char,
            MappingEvidence.reason,
            ContextCheckpointMapping.created_at,
        )
        .join(ContextChunk, ContextChunk.id == ContextCheckpointMapping.context_chunk_id)
        .join(DiscoveryCheckpoint, DiscoveryCheckpoint.id == ContextCheckpointMapping.checkpoint_id)
        .join(DiscoveryPillar, DiscoveryPillar.id == DiscoveryCheckpoint.pillar_id)
        .join(MappingEvidence, MappingEvidence.mapping_id == ContextCheckpointMapping.id)
        .where(ContextCheckpointMapping.is_active == true(), *filters)
        .order_by(ContextChunk.chunk_number, DiscoveryCheckpoint.sort_order, ContextCheckpointMapping.id)
    ).all()
    return [
        {
            "id": row[0],
            "project_id": row[1],
            "context_chunk_id": row[2],
            "context_content_id": row[3],
            "chunk_number": row[4],
            "checkpoint_id": row[5],
            "checkpoint_code": row[6],
            "checkpoint_name": row[7],
            "pillar_name": row[8],
            "evidence_quote": row[9],
            "evidence_start_char": row[10],
            "evidence_end_char": row[11],
            "reason": row[12],
            "created_at": row[13],
        }
        for row in rows
    ]
