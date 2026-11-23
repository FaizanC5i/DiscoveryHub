"""
Sends new chunks to the Helper Agent and saves the checkpoint matches it returns.

Analogy: the sorting office. Each parcel (chunk) is labelled as "waiting", then "being
sorted", then "sorted" or "nothing for it here". Parcels go out in trays of a fixed size
(MAPPING_BATCH_SIZE). If the courier fails, the tray is retried twice more, and if that
fails too it is marked failed with the reason, while the other trays carry on.

Correctness:
- Chunking commits before mapping starts, so a mapping failure never undoes chunking.
- A chunk is claimed with one atomic UPDATE. A chunk that is already IN_PROGRESS, MAPPED,
  or NO_MATCH is never claimed again, so repeated triggers do not duplicate work.
- A batch's mapping rows and status changes commit together, or not at all.
"""

import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass

from fastapi import BackgroundTasks
from sqlalchemy import select, true, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import utc_now
from app.db.models import (
    AgentRun,
    ContextChunk,
    ContextCheckpointMapping,
    ContextContent,
    ContextSource,
    Agent,
    MappingEvidence,
    Project,
)
from app.db.session import get_session_factory
from app.services import pillar_dispatch_service
from app.services.agent_client import AgentError, call_helper_agent, call_with_retry
from app.services.answers import answer_pipeline
from app.services.answers.user_context import pending_mapping_count
from app.services.mapping_payload_service import build_mapping_request
from app.services.mapping_validation_service import (
    BatchValidation,
    MappingResponseError,
    find_checkpoint_output,
    validate_batch,
)

log = logging.getLogger(__name__)

HELPER_AGENT_CODE = "HELPER_AGENT"
CLAIMABLE_STATUSES = ("PENDING", "FAILED")
GENERIC_FAILURE = "The chunks could not be mapped. Please try again."


@dataclass(frozen=True)
class BatchOutcome:
    agent_run_id: int
    project_id: int
    chunk_ids: list[int]
    kept: int
    dropped: int
    skipped_existing: int


def enqueue_chunk_mapping(background: BackgroundTasks, chunk_ids: list[int]) -> None:
    """
    Queue mapping for these chunks. The work runs after the HTTP response is sent.

    Callers use only this function, so moving to a real queue later means changing this
    one body and nothing that calls it.
    """
    if chunk_ids:
        background.add_task(run_mapping_job, list(chunk_ids))


def run_mapping_job(chunk_ids: list[int]) -> None:
    """Claim the chunks that need mapping, then map them in batches. Never raises."""
    sessions = get_session_factory()
    with sessions() as db:
        claimed = _claim_chunks(db, chunk_ids)

    batch_size = get_settings().mapping_batch_size
    for project_id, ids in claimed:
        for start in range(0, len(ids), batch_size):
            map_batch(project_id, ids[start : start + batch_size])

    for project_id, ids in claimed:
        _start_user_discovery_if_ready(project_id, ids)


def map_batch(project_id: int, chunk_ids: list[int]) -> BatchOutcome | None:
    """
    Run one agent call for these chunks and save the result.

    Returns the outcome, or None when the batch failed. Failure is recorded on the chunks,
    so the caller never needs to handle it.
    """
    sessions = get_session_factory()
    with sessions() as db:
        chunks = _load_chunks(db, chunk_ids)
        content_texts = _content_texts(db, {chunk["context_content_id"] for chunk in chunks})
        payload = build_mapping_request(db, project_id, chunks)
        checkpoints = {cp["id"]: cp for cp in payload["discovery_checkpoints"]}
        helper_agent_id = _helper_agent_id(db)
        run = AgentRun(
            project_id=project_id,
            agent_id=helper_agent_id,
            batch_id=_new_batch_id(),
            status="running",
            chunk_count=len(chunks),
        )
        db.add(run)
        db.commit()
        agent_run_id = run.id

    started = time.monotonic()
    log.info("Mapping batch %s: sending %d chunk(s) to the Helper Agent.", agent_run_id, len(chunk_ids))
    try:
        reply = _call_with_retry(payload, agent_run_id)
        output = find_checkpoint_output(reply)
        if output is None:
            raise MappingResponseError("The agent reply has no chunk_results.")
        validation = validate_batch(chunks, checkpoints, output, content_texts)
        kept, skipped = _save_success(
            project_id, agent_run_id, helper_agent_id, chunk_ids, validation, reply, output
        )
    except Exception as exc:
        _record_failure(agent_run_id, chunk_ids, exc)
        log.warning(
            "Mapping batch %s failed after %.1fs for chunks %s: %s",
            agent_run_id, time.monotonic() - started, chunk_ids, _failure_message(exc),
        )
        return None

    outcome = BatchOutcome(
        agent_run_id=agent_run_id,
        project_id=project_id,
        chunk_ids=chunk_ids,
        kept=kept,
        dropped=validation.dropped,
        skipped_existing=skipped,
    )
    log.info(
        "Mapping batch %s succeeded in %.1fs: chunks=%s kept=%d dropped=%d skipped_existing=%d",
        outcome.agent_run_id, time.monotonic() - started, chunk_ids,
        outcome.kept, outcome.dropped, outcome.skipped_existing,
    )
    if outcome.kept:
        _dispatch_to_pillar_agents(agent_run_id)
    return outcome


def _start_user_discovery_if_ready(project_id: int, chunk_ids: list[int]) -> None:
    """
    After mapping finishes, start a User Discovery run on the chunks this job just mapped,
    if no chunk is still pending and no run is already in progress.
    Failures here are logged and never affect the mapping outcome.
    """
    try:
        with get_session_factory()() as db:
            if pending_mapping_count(db, project_id):
                return
            new_mapped = set(
                db.scalars(
                    select(ContextChunk.id).where(
                        ContextChunk.id.in_(chunk_ids),
                        ContextChunk.mapping_status == "MAPPED",
                    )
                )
            )
            if not new_mapped:
                return
            if answer_pipeline.is_running(project_id):
                return
        log.info("Auto-starting User Discovery for project %s on %d newly mapped chunks.", project_id, len(new_mapped))
        threading.Thread(
            target=answer_pipeline.run_in_background,
            args=(project_id, None, new_mapped),
            daemon=True,
            name=f"user-discovery-{project_id}",
        ).start()
    except Exception:
        log.exception("Could not auto-start User Discovery for project %s", project_id)


def _dispatch_to_pillar_agents(agent_run_id: int) -> None:
    """
    Send this batch's new mappings to the pillar agents. The mappings are already committed,
    so a dispatch problem is logged and never undoes or fails the mapping.
    """
    if not get_settings().pillar_dispatch_outbox:
        return
    try:
        pillar_dispatch_service.dispatch_mapping_run(agent_run_id)
    except Exception:
        log.exception("Could not dispatch mapping batch %s to the pillar agents", agent_run_id)


def retry_chunk_ids(db: Session, content_id: int) -> list[int]:
    """Chunks of one content that are FAILED or PENDING, the only ones a manual retry may send."""
    return list(
        db.scalars(
            select(ContextChunk.id)
            .where(
                ContextChunk.context_content_id == content_id,
                ContextChunk.mapping_status.in_(CLAIMABLE_STATUSES),
            )
            .order_by(ContextChunk.chunk_number)
        )
    )


# --- helpers -----------------------------------------------------------------


def _claim_chunks(db: Session, chunk_ids: list[int]) -> list[tuple[int, list[int]]]:
    """
    Flip the claimable chunks to IN_PROGRESS in one UPDATE and return those rows.

    Correctness: the WHERE clause and the change happen in one statement, so two jobs
    racing for the same chunk cannot both win it.
    """
    claimed_ids = list(
        db.scalars(
            update(ContextChunk)
            .where(ContextChunk.id.in_(chunk_ids), ContextChunk.mapping_status.in_(CLAIMABLE_STATUSES))
            .values(mapping_status="IN_PROGRESS")
            .returning(ContextChunk.id)
        )
    )
    db.commit()
    if not claimed_ids:
        return []

    rows = db.execute(
        select(ContextChunk.id, Project.id)
        .join(ContextContent, ContextContent.id == ContextChunk.context_content_id)
        .join(ContextSource, ContextSource.id == ContextContent.context_source_id)
        .join(Project, Project.id == ContextSource.project_id)
        .where(ContextChunk.id.in_(claimed_ids))
        .order_by(ContextChunk.id)
    ).all()

    grouped: dict[int, list[int]] = {}
    for chunk_id, project_id in rows:
        grouped.setdefault(project_id, []).append(chunk_id)
    return list(grouped.items())


def _new_batch_id() -> str:
    return f"BATCH-{utc_now():%Y%m%d}-{uuid.uuid4().hex[:8].upper()}"


def _load_chunks(db: Session, chunk_ids: list[int]) -> list[dict]:
    rows = db.execute(
        select(
            ContextChunk.id,
            ContextChunk.context_content_id,
            ContextChunk.chunk_number,
            ContextChunk.chunk_text,
            ContextChunk.page_number,
            ContextChunk.start_char,
        )
        .where(ContextChunk.id.in_(chunk_ids))
        .order_by(ContextChunk.id)
    ).all()
    return [
        {
            "id": row.id,
            "context_content_id": row.context_content_id,
            "chunk_number": row.chunk_number,
            "chunk_text": row.chunk_text,
            "page_number": row.page_number,
            "start_char": row.start_char,
        }
        for row in rows
    ]


def _content_texts(db: Session, content_ids: set[int]) -> dict[int, str]:
    rows = db.execute(
        select(ContextContent.id, ContextContent.content_text).where(ContextContent.id.in_(content_ids))
    ).all()
    return {row.id: row.content_text for row in rows}


def _helper_agent_id(db: Session) -> int:
    agent_id = db.scalar(select(Agent.id).where(Agent.agent_code == HELPER_AGENT_CODE))
    if agent_id is None:
        raise RuntimeError("The Helper Agent is not registered. Run the database migrations.")
    return agent_id


def _call_with_retry(payload: dict, agent_run_id: int) -> dict:
    return call_with_retry(lambda: call_helper_agent(payload), f"Mapping batch {agent_run_id}")


def _save_success(
    project_id: int,
    agent_run_id: int,
    helper_agent_id: int,
    chunk_ids: list[int],
    validation: BatchValidation,
    reply: dict,
    output: dict,
) -> tuple[int, int]:
    """Write the mappings, evidence, chunk statuses and run result in one transaction."""
    sessions = get_session_factory()
    with sessions() as db:
        try:
            active_pairs = set(
                db.execute(
                    select(ContextCheckpointMapping.context_chunk_id, ContextCheckpointMapping.checkpoint_id)
                    .where(
                        ContextCheckpointMapping.context_chunk_id.in_(chunk_ids),
                        ContextCheckpointMapping.is_active == true(),
                    )
                ).all()
            )
            kept = 0
            skipped = 0
            for match in validation.matches:
                pair = (match.chunk_id, match.checkpoint_id)
                if pair in active_pairs:
                    skipped += 1
                    continue
                mapping = ContextCheckpointMapping(
                    project_id=project_id,
                    context_chunk_id=match.chunk_id,
                    checkpoint_id=match.checkpoint_id,
                    agent_run_id=agent_run_id,
                    mapped_by_agent_id=helper_agent_id,
                    is_active=True,
                )
                mapping.evidence.append(
                    MappingEvidence(
                        evidence_quote=match.evidence_quote,
                        reason=match.reason,
                        evidence_start_char=match.evidence_start_char,
                        evidence_end_char=match.evidence_end_char,
                    )
                )
                db.add(mapping)
                active_pairs.add(pair)
                kept += 1
            db.flush()

            now = utc_now()
            mapped_ids = sorted(validation.matched_chunk_ids)
            unmatched_ids = [chunk_id for chunk_id in chunk_ids if chunk_id not in validation.matched_chunk_ids]
            for status, ids in (("MAPPED", mapped_ids), ("NO_MATCH", unmatched_ids)):
                if ids:
                    db.execute(
                        update(ContextChunk)
                        .where(ContextChunk.id.in_(ids))
                        .values(
                            mapping_status=status,
                            mapped_at=now,
                            mapping_error=None,
                            mapping_attempts=ContextChunk.mapping_attempts + 1,
                        )
                    )

            run = db.get(AgentRun, agent_run_id)
            metainfo = reply.get("metainfo") if isinstance(reply.get("metainfo"), dict) else {}
            models = metainfo.get("model")
            run.status = "succeeded"
            run.completed_at = now
            run.model = models[0] if isinstance(models, list) and models else None
            run.prompt_tokens = metainfo.get("prompt_tokens")
            run.completion_tokens = metainfo.get("completion_tokens")
            run.raw_output = json.dumps(output, ensure_ascii=False)
            db.commit()
            return kept, skipped
        except Exception:
            db.rollback()
            raise


def _record_failure(agent_run_id: int, chunk_ids: list[int], exc: Exception) -> None:
    """Mark the run and its chunks failed. Other batches are not affected."""
    message = _failure_message(exc)
    if not isinstance(exc, (AgentError, MappingResponseError)):
        log.exception("Unexpected error while mapping batch %s", agent_run_id)
    sessions = get_session_factory()
    with sessions() as db:
        run = db.get(AgentRun, agent_run_id)
        if run is not None:
            run.status = "failed"
            run.error_message = message[:1000]
            run.completed_at = utc_now()
        db.execute(
            update(ContextChunk)
            .where(ContextChunk.id.in_(chunk_ids))
            .values(
                mapping_status="FAILED",
                mapping_error=message,
                mapping_attempts=ContextChunk.mapping_attempts + 1,
            )
        )
        db.commit()


def _failure_message(exc: Exception) -> str:
    """Errors from the agent or the reply are safe to store; anything else gets a generic message."""
    if isinstance(exc, (AgentError, MappingResponseError)):
        return str(exc)
    return GENERIC_FAILURE
