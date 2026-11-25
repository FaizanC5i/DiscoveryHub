"""
Runs the User Discovery agent on a project's mapped evidence and stores what it returns.

Analogy: the case desk. One request goes to the specialist with every checkpoint that has
evidence. Each opinion that passes the checks becomes a proposal waiting for the owner. If the
call fails, or anything goes wrong while storing, nothing from that run is kept and the run is
recorded as failed.
"""

import json
import logging
import threading
import uuid
from dataclasses import dataclass, field
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.time import utc_now
from app.db.models import (
    Agent,
    AgentRun,
    AgentRunCheckpoint,
    CheckpointAnswerProposal,
    ProjectCheckpointAnswer,
    ProposalEvidence,
)
from app.db.session import get_session_factory
from app.services.answers.common import ReviewError, latest_version_number, require_owner
from app.services.answers.user_agent import (
    AgentCallError,
    ContractError,
    ParseResult,
    SentCheckpoint,
    call_user_agent,
    final_output,
    parse_proposals,
)
from app.services.answers.user_context import (
    DB_AGENT_CODE,
    active_user_checkpoints,
    build_agent_batch,
    pending_mapping_count,
    project_mapping_rows,
)
from app.services.answers.user_agent import ParsedProposal

log = logging.getLogger(__name__)

RUN_TYPE = "pillar_answer"
ANSWER_PENDING_REVIEW = "PENDING_REVIEW"
ANSWER_APPROVED = "APPROVED"
ANSWER_NOT_STARTED = "NOT_STARTED"
PROPOSAL_PENDING = "PENDING"
PROPOSAL_SUPERSEDED = "SUPERSEDED"

_locks: dict[int, threading.Lock] = {}
_locks_guard = threading.Lock()


def lock_for(project_id: int) -> threading.Lock:
    with _locks_guard:
        return _locks.setdefault(project_id, threading.Lock())


def is_running(project_id: int) -> bool:
    return lock_for(project_id).locked()


@dataclass
class RunOutcome:
    status: str
    run_id: int | None = None
    processed: list[dict] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def request_run(db: Session, owner_id: int, project_id: int, checkpoint_ids: list[int] | None = None) -> None:
    """Checks that a run may start now. Raises ReviewError when it may not."""
    require_owner(db, owner_id, project_id)
    if is_running(project_id):
        raise ReviewError(409, "RUN_ALREADY_IN_PROGRESS", "A User Discovery run is already in progress.")
    pending = pending_mapping_count(db, project_id)
    if pending:
        raise ReviewError(
            409,
            "MAPPING_IN_PROGRESS",
            f"{pending} chunks are still being mapped. Run User Discovery after mapping has finished.",
        )
    if not project_mapping_rows(db, project_id, checkpoint_ids):
        raise ReviewError(422, "NO_EVIDENCE", "There is no mapped evidence to send.")


def save_owner_input(db: Session, owner_id: int, project_id: int, checkpoint_id: int, text: str) -> None:
    """Stores the owner's own answer for one checkpoint, to be sent with the next run for it."""
    require_owner(db, owner_id, project_id)
    cleaned = text.strip()
    if not cleaned:
        raise ReviewError(422, "EMPTY_INPUT", "Write something before sending.")
    if checkpoint_id not in active_user_checkpoints(db):
        raise ReviewError(404, "CHECKPOINT_NOT_FOUND", "This checkpoint is not part of User Discovery.")
    if is_running(project_id):
        raise ReviewError(409, "RUN_ALREADY_IN_PROGRESS", "A User Discovery run is already in progress.")
    pending = pending_mapping_count(db, project_id)
    if pending:
        raise ReviewError(409, "MAPPING_IN_PROGRESS", f"{pending} chunks are still being mapped.")
    answer = get_or_create_answer(db, project_id, checkpoint_id)
    answer.owner_input = cleaned
    answer.updated_at = utc_now()
    db.commit()


def run_in_background(project_id: int, checkpoint_ids: list[int] | None, chunk_ids: set[int] | None = None) -> None:
    lock = lock_for(project_id)
    if not lock.acquire(blocking=False):
        log.info("User Discovery run already in progress for project %s.", project_id)
        return
    try:
        with get_session_factory()() as db:
            execute_run(db, project_id, checkpoint_ids, chunk_ids=chunk_ids)
    except Exception:
        log.exception("User Discovery run crashed for project %s", project_id)
    finally:
        lock.release()


def get_or_create_answer(db: Session, project_id: int, checkpoint_id: int) -> ProjectCheckpointAnswer:
    answer = db.scalar(
        select(ProjectCheckpointAnswer).where(
            ProjectCheckpointAnswer.project_id == project_id,
            ProjectCheckpointAnswer.checkpoint_id == checkpoint_id,
        )
    )
    if answer is None:
        answer = ProjectCheckpointAnswer(
            project_id=project_id,
            checkpoint_id=checkpoint_id,
            status=ANSWER_NOT_STARTED,
            is_completed=False,
        )
        db.add(answer)
        db.flush()
    return answer


def execute_run(
    db: Session,
    project_id: int,
    checkpoint_ids: list[int] | None = None,
    agent_call=call_user_agent,
    chunk_ids: set[int] | None = None,
) -> RunOutcome:
    built = build_agent_batch(db, project_id, checkpoint_ids, chunk_ids)
    if built is None:
        return RunOutcome(status="nothing_to_run")

    agent_id = db.scalar(select(Agent.id).where(Agent.agent_code == DB_AGENT_CODE))
    if agent_id is None:
        raise RuntimeError("The User Discovery agent row is missing. Run the database migrations.")

    run = AgentRun(
        project_id=project_id,
        agent_id=agent_id,
        run_type=RUN_TYPE,
        status="running",
        chunk_count=built.chunk_count,
        batch_id=f"PILLAR-{uuid.uuid4().hex[:12]}",
    )
    db.add(run)
    db.commit()
    run_id = run.id

    raw_text: str | None = None
    log.info(
        "User Discovery run %s: sending %d checkpoint(s) with %d evidence chunk(s) [%s].",
        run_id,
        len(built.sent),
        built.chunk_count,
        ", ".join(item.code for item in built.sent),
    )
    try:
        data = agent_call(built.payload)
        raw_text = json.dumps(data, ensure_ascii=False)
        log.info("User Discovery run %s: agent responded for %d checkpoint(s).", run_id, len(built.sent))
        result = parse_proposals(final_output(data), built.sent)
        outcome = _store(db, project_id, run_id, built.sent, result, raw_text)
        log.info(
            "User Discovery run %s finished: %d proposal(s) stored [%s]; %d failed [%s].",
            run_id,
            len(outcome.processed),
            ", ".join(item["checkpoint_code"] for item in outcome.processed) or "-",
            len(outcome.failed),
            "; ".join(f"{item['checkpoint_code']}: {item['error']}" for item in outcome.failed) or "-",
        )
        for warning in result.warnings:
            log.info("User Discovery run %s warning: %s", run_id, warning)
        return outcome
    except (AgentCallError, ContractError) as exc:
        log.warning("User Discovery run %s failed: %s", run_id, exc)
        return _fail_run(db, run_id, str(exc), built.sent, raw_text)
    except Exception as exc:
        log.exception("User Discovery run %s crashed", run_id)
        return _fail_run(db, run_id, f"Unexpected error: {type(exc).__name__}", built.sent, raw_text)


def _store(
    db: Session,
    project_id: int,
    run_id: int,
    sent: list[SentCheckpoint],
    result: ParseResult,
    raw_text: str,
) -> RunOutcome:
    """Stores every accepted proposal and the run result in one transaction."""
    processed: list[dict] = []
    failed: list[dict] = []
    for item in sent:
        if item.id in result.accepted:
            answer = get_or_create_answer(db, project_id, item.id)
            proposal = _store_proposal(db, run_id, answer, result.accepted[item.id], item)
            db.add(AgentRunCheckpoint(agent_run_id=run_id, checkpoint_id=item.id, status="ANSWERED"))
            processed.append({"checkpoint_code": item.code, "proposal_id": proposal.id})
        else:
            message = result.failures.get(item.id, "No valid proposal.")
            db.add(AgentRunCheckpoint(agent_run_id=run_id, checkpoint_id=item.id, status="FAILED"))
            failed.append({"checkpoint_code": item.code, "error": message})

    run = db.get(AgentRun, run_id)
    run.status = "succeeded"
    run.raw_output = raw_text
    run.completed_at = utc_now()
    run.error_message = _summary(failed)
    db.commit()
    return RunOutcome(status="succeeded", run_id=run_id, processed=processed, failed=failed, warnings=result.warnings)


def _store_proposal(
    db: Session,
    run_id: int,
    answer: ProjectCheckpointAnswer,
    parsed: ParsedProposal,
    item: SentCheckpoint,
) -> CheckpointAnswerProposal:
    previous = db.scalar(
        select(CheckpointAnswerProposal).where(
            CheckpointAnswerProposal.current_answer_id == answer.id,
            CheckpointAnswerProposal.status == PROPOSAL_PENDING,
        )
    )
    proposal = CheckpointAnswerProposal(
        current_answer_id=answer.id,
        agent_run_id=run_id,
        base_version_number=latest_version_number(db, answer.id),
        proposed_answer=parsed.proposed_answer,
        completion_score=Decimal(str(parsed.completion_score)),
        status=PROPOSAL_PENDING,
        agent_status=parsed.agent_status,
        is_completed=parsed.is_completed,
        missing_information=json.dumps(parsed.missing_information, ensure_ascii=False),
        clarification_questions=json.dumps(parsed.clarification_questions, ensure_ascii=False),
    )
    if previous is not None:
        previous.status = PROPOSAL_SUPERSEDED
        db.flush()  # frees the single PENDING slot before the new row is inserted
    db.add(proposal)
    db.flush()
    if previous is not None:
        previous.superseded_by_proposal_id = proposal.id

    _link_evidence(db, proposal, parsed, item)
    answer.status = ANSWER_APPROVED if answer.approved_at else ANSWER_PENDING_REVIEW
    db.flush()
    return proposal


def _link_evidence(db: Session, proposal: CheckpointAnswerProposal, parsed: ParsedProposal, item: SentCheckpoint) -> None:
    """Links the chunks the agent cited. When it cites none, every mapped chunk of the checkpoint is linked."""
    reasons: dict[int, str] = {}
    for evidence in parsed.evidence:
        reasons.setdefault(evidence.chunk_id, evidence.reason)
    chosen = list(reasons) or sorted(item.chunk_ids)
    for chunk_id in chosen:
        db.add(ProposalEvidence(
            proposal_id=proposal.id,
            context_chunk_id=chunk_id,
            mapping_id=item.mapping_by_chunk[chunk_id],
            reason=reasons.get(chunk_id) or None,
        ))


def _fail_run(
    db: Session,
    run_id: int,
    message: str,
    sent: list[SentCheckpoint],
    raw_text: str | None,
) -> RunOutcome:
    """Keeps the run record and nothing else from this run."""
    db.rollback()
    run = db.get(AgentRun, run_id)
    run.status = "failed"
    run.error_message = message[:1000]
    run.raw_output = raw_text
    run.completed_at = utc_now()
    for item in sent:
        db.add(AgentRunCheckpoint(agent_run_id=run_id, checkpoint_id=item.id, status="FAILED"))
    db.commit()
    return RunOutcome(
        status="failed",
        run_id=run_id,
        failed=[{"checkpoint_code": item.code, "error": message} for item in sent],
    )


def _summary(failed: list[dict]) -> str | None:
    if not failed:
        return None
    return "; ".join(f"{f['checkpoint_code']}: {f['error']}" for f in failed)[:1000]