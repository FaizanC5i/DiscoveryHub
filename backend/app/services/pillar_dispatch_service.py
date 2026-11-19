"""
Sends each batch of new checkpoint mappings to the right pillar agent, straight away.

When the Helper Agent finishes a batch, its mappings (chunk -> checkpoint) are saved in one
transaction. Right after that commit, this module:

1. reads the mappings that batch created, with the chunk text, the source and the evidence,
   plus the existing answer of every checkpoint involved (project_checkpoint_answers), so the
   agent can update that answer instead of starting again,
2. looks up the pillar of each mapping's checkpoint (USER, DATA, TECH),
3. groups them into one package per pillar agent,
4. hands each package to the outbox.

Only the batch's own new mappings are sent. A pair the Helper had already mapped earlier is
skipped by the mapping job, so it is never sent twice.

The pillar agents do not exist yet, so the outbox writes each package to a JSON file
(backend/<pillar_dispatch_outbox>/project_<id>/<batch_id>/<AGENT_CODE>.json). When an agent
is ready, only the outbox changes: the grouping stays the same.

Analogy: a sorting office that works parcel tray by parcel tray. As soon as a tray has been
labelled, its parcels are put into the pigeonhole of each label they carry. Nobody waits for
the day's last tray.
"""

import json
import logging
from collections.abc import Callable
from pathlib import Path

from sqlalchemy import select, true
from sqlalchemy.orm import Session

from app.core.config import BACKEND_DIR, get_settings
from app.core.time import utc_now
from app.db.models import (
    Agent,
    AgentRun,
    ContextChunk,
    ContextCheckpointMapping,
    ContextContent,
    ContextSource,
    DiscoveryCheckpoint,
    DiscoveryPillar,
    MappingEvidence,
    ProjectCheckpointAnswer,
)
from app.db.session import get_session_factory

log = logging.getLogger(__name__)

# Receives one package for one pillar agent.
Sender = Callable[[dict], None]


def dispatch_mapping_run(helper_agent_run_id: int, send: Sender | None = None) -> list[dict]:
    """
    Group the mappings one Helper batch created and send one package per pillar agent.

    Returns the packages that were sent (empty when the batch created no active mappings).
    Raises on a database or outbox error; the mapping job catches it so mapping is unaffected.
    """
    sessions = get_session_factory()
    with sessions() as db:
        run = db.get(AgentRun, helper_agent_run_id)
        if run is None:
            raise ValueError(f"Agent run {helper_agent_run_id} does not exist.")
        rows = _batch_rows(db, helper_agent_run_id)
        agents = _pillar_agents(db)
        answers = _existing_answers(db, run.project_id, {row["checkpoint_id"] for row in rows})
        batch = {
            "project_id": run.project_id,
            "batch_id": run.batch_id or f"RUN-{run.id}",
            "helper_agent_run_id": run.id,
        }

    packages = group_batch_by_pillar(batch, rows, agents, created_at=utc_now().isoformat(), existing_answers=answers)
    _check_nothing_left_out(rows, packages, helper_agent_run_id)

    sender = send or json_file_outbox()
    for package in packages:
        sender(package)
    log.info(
        "Dispatched mapping batch %s: %s",
        helper_agent_run_id,
        ", ".join(f"{p['pillar_code']}={p['chunk_count']} chunks" for p in packages) or "nothing new",
    )
    return packages


# --- pure logic (no database), unit tested ------------------------------------------


def group_batch_by_pillar(
    batch: dict,
    rows: list[dict],
    agents: dict[int, dict],
    created_at: str,
    existing_answers: dict[int, dict] | None = None,
) -> list[dict]:
    """
    Build one package per pillar that has at least one mapping in this batch.

    batch:  {"project_id", "batch_id", "helper_agent_run_id"}.
    rows:   one row per (mapping, evidence), in a stable order, with the checkpoint, its
            pillar, and the chunk's text and source. evidence_quote is None when a mapping
            has no evidence row.
    agents: pillar_id -> {"agent_id", "agent_code"} for the pillar agents that exist.
    existing_answers: checkpoint_id -> {"answer", "status"} from project_checkpoint_answers. Each
            checkpoint carries its existing answer (None when there is none yet) next to the new
            chunks, so the agent updates that answer instead of starting from nothing.

    A chunk mapped to checkpoints of two pillars goes into both packages. A chunk mapped to
    two checkpoints of the same pillar appears under each checkpoint, and is counted once.
    Only checkpoints this batch touched are listed, because each batch adds to what the
    agent already has.
    """
    existing_answers = existing_answers or {}
    packages: dict[int, dict] = {}
    checkpoint_slots: dict[tuple[int, int], dict] = {}
    chunk_slots: dict[tuple[int, int, int], dict] = {}

    for row in rows:
        pillar_id = row["pillar_id"]
        package = packages.get(pillar_id)
        if package is None:
            agent = agents.get(pillar_id) or {}
            package = {
                **batch,
                "created_at": created_at,
                "pillar_id": pillar_id,
                "pillar_code": row["pillar_code"],
                "pillar_name": row["pillar_name"],
                "agent_id": agent.get("agent_id"),
                "agent_code": agent.get("agent_code"),
                "checkpoint_count": 0,
                "chunk_count": 0,
                "mapping_count": 0,
                "checkpoints": [],
            }
            packages[pillar_id] = package

        checkpoint_key = (pillar_id, row["checkpoint_id"])
        checkpoint = checkpoint_slots.get(checkpoint_key)
        if checkpoint is None:
            checkpoint = {
                "checkpoint_id": row["checkpoint_id"],
                "code": row["checkpoint_code"],
                "name": row["checkpoint_name"],
                "question": row["question"],
                "why_it_matters": row["why_it_matters"],
                "sort_order": row["sort_order"],
                "existing_answer": (existing_answers.get(row["checkpoint_id"]) or {}).get("answer"),
                "existing_answer_status": (existing_answers.get(row["checkpoint_id"]) or {}).get("status"),
                "chunks": [],
            }
            checkpoint_slots[checkpoint_key] = checkpoint
            package["checkpoints"].append(checkpoint)

        chunk_key = (pillar_id, row["checkpoint_id"], row["chunk_id"])
        chunk = chunk_slots.get(chunk_key)
        if chunk is None:
            chunk = {
                "chunk_id": row["chunk_id"],
                "chunk_number": row["chunk_number"],
                "mapping_id": row["mapping_id"],
                "source_id": row["source_id"],
                "source_title": row["source_title"],
                "page_number": row["page_number"],
                "chunk_text": row["chunk_text"],
                "evidence": [],
            }
            chunk_slots[chunk_key] = chunk
            checkpoint["chunks"].append(chunk)
        if row.get("evidence_quote") is not None:
            chunk["evidence"].append(
                {
                    "quote": row["evidence_quote"],
                    "reason": row["evidence_reason"],
                    "start_char": row["evidence_start_char"],
                    "end_char": row["evidence_end_char"],
                }
            )

    result = sorted(packages.values(), key=lambda p: p["pillar_id"])
    for package in result:
        package["checkpoints"].sort(key=lambda c: (c["sort_order"], c["checkpoint_id"]))
        package["checkpoint_count"] = len(package["checkpoints"])
        chunks = [chunk for c in package["checkpoints"] for chunk in c["chunks"]]
        package["chunk_count"] = len({chunk["chunk_id"] for chunk in chunks})
        package["mapping_count"] = len({chunk["mapping_id"] for chunk in chunks})
    return result


def missing_mapping_ids(rows: list[dict], packages: list[dict]) -> list[int]:
    """Mappings in the batch that did not reach any package. Always empty unless grouping is broken."""
    sent = {
        chunk["mapping_id"]
        for package in packages
        for checkpoint in package["checkpoints"]
        for chunk in checkpoint["chunks"]
    }
    return sorted({row["mapping_id"] for row in rows} - sent)


# --- outbox -------------------------------------------------------------------------


def json_file_outbox(folder: Path | None = None) -> Sender:
    """
    Testing outbox: writes each package to <folder>/project_<id>/<batch_id>/<AGENT_CODE>.json.

    The folder holds client document text, so it is git-ignored and must not be shared.
    """
    root = folder or BACKEND_DIR / get_settings().pillar_dispatch_outbox

    def _send(package: dict) -> None:
        target = root / f"project_{package['project_id']}" / package["batch_id"]
        target.mkdir(parents=True, exist_ok=True)
        name = package["agent_code"] or f"{package['pillar_code']}_NO_AGENT"
        (target / f"{name}.json").write_text(
            json.dumps(package, indent=2, ensure_ascii=False, default=str), encoding="utf-8"
        )

    return _send


# --- database reads -----------------------------------------------------------------


def _batch_rows(db: Session, helper_agent_run_id: int) -> list[dict]:
    """Active mappings this run created, on documents that have not been removed, one row per evidence."""
    rows = db.execute(
        select(
            ContextCheckpointMapping.id,
            DiscoveryCheckpoint.id,
            DiscoveryCheckpoint.code,
            DiscoveryCheckpoint.name,
            DiscoveryCheckpoint.question,
            DiscoveryCheckpoint.why_it_matters,
            DiscoveryCheckpoint.sort_order,
            DiscoveryPillar.id,
            DiscoveryPillar.code,
            DiscoveryPillar.name,
            ContextChunk.id,
            ContextChunk.chunk_number,
            ContextChunk.chunk_text,
            ContextChunk.page_number,
            ContextSource.id,
            ContextSource.title,
            MappingEvidence.evidence_quote,
            MappingEvidence.reason,
            MappingEvidence.evidence_start_char,
            MappingEvidence.evidence_end_char,
        )
        .join(DiscoveryCheckpoint, DiscoveryCheckpoint.id == ContextCheckpointMapping.checkpoint_id)
        .join(DiscoveryPillar, DiscoveryPillar.id == DiscoveryCheckpoint.pillar_id)
        .join(ContextChunk, ContextChunk.id == ContextCheckpointMapping.context_chunk_id)
        .join(ContextContent, ContextContent.id == ContextChunk.context_content_id)
        .join(ContextSource, ContextSource.id == ContextContent.context_source_id)
        .outerjoin(MappingEvidence, MappingEvidence.mapping_id == ContextCheckpointMapping.id)
        .where(
            ContextCheckpointMapping.agent_run_id == helper_agent_run_id,
            ContextCheckpointMapping.is_active == true(),
            ContextSource.deleted_at.is_(None),
        )
        .order_by(ContextSource.id, ContextChunk.chunk_number, ContextCheckpointMapping.id, MappingEvidence.id)
    ).all()
    return [
        {
            "mapping_id": r[0],
            "checkpoint_id": r[1],
            "checkpoint_code": r[2],
            "checkpoint_name": r[3],
            "question": r[4],
            "why_it_matters": r[5],
            "sort_order": r[6],
            "pillar_id": r[7],
            "pillar_code": r[8],
            "pillar_name": r[9],
            "chunk_id": r[10],
            "chunk_number": r[11],
            "chunk_text": r[12],
            "page_number": r[13],
            "source_id": r[14],
            "source_title": r[15],
            "evidence_quote": r[16],
            "evidence_reason": r[17],
            "evidence_start_char": r[18],
            "evidence_end_char": r[19],
        }
        for r in rows
    ]


def _existing_answers(db: Session, project_id: int, checkpoint_ids: set[int]) -> dict[int, dict]:
    """The current answer of each checkpoint in this project (project_checkpoint_answers)."""
    if not checkpoint_ids:
        return {}
    rows = db.execute(
        select(
            ProjectCheckpointAnswer.checkpoint_id,
            ProjectCheckpointAnswer.current_answer,
            ProjectCheckpointAnswer.status,
        ).where(
            ProjectCheckpointAnswer.project_id == project_id,
            ProjectCheckpointAnswer.checkpoint_id.in_(checkpoint_ids),
        )
    ).all()
    return {checkpoint_id: {"answer": answer, "status": status} for checkpoint_id, answer, status in rows}


def _pillar_agents(db: Session) -> dict[int, dict]:
    """The agent of each pillar (seeded by migration 009). The Helper Agent has no pillar."""
    rows = db.execute(select(Agent.pillar_id, Agent.id, Agent.agent_code).where(Agent.pillar_id.is_not(None))).all()
    return {pillar_id: {"agent_id": agent_id, "agent_code": code} for pillar_id, agent_id, code in rows}


def _check_nothing_left_out(rows: list[dict], packages: list[dict], helper_agent_run_id: int) -> None:
    missing = missing_mapping_ids(rows, packages)
    if missing:
        raise RuntimeError(f"Mapping batch {helper_agent_run_id}: mappings {missing} reached no pillar package.")
    for package in packages:
        if package["agent_code"] is None:
            log.warning(
                "Mapping batch %s: pillar %s has no agent in the agents table; package saved without one.",
                helper_agent_run_id, package["pillar_code"],
            )
