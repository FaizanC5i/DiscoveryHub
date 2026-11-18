"""
BRD generation from the project's APPROVED User Discovery answers.

Which answers: every approved answer of the pillars listed for the BRD in artifact_type_pillars
(User Discovery only). A section reads only its own checkpoints when artifact_section_checkpoints
has rows for it; otherwise it reads all of them (the case for every BRD section today).

Kept up to date: approving a User Discovery answer calls refresh_brd(), which regenerates the BRD
in the background. Answers approved while a run is busy are picked up by one more run at the end.
The new text arrives as proposals, so approved BRD content is never overwritten.

Flow (same as the stand-alone BRD app; only the input changed):
1. generate      -> one agent call writes all 14 sections from every approved answer.
                    Empty sections then get up to 3 clarification questions each.
2. clarify       -> the agent asks up to 3 questions for one section.
3. regenerate    -> the agent rewrites one section from the answers that feed it
                    (artifact_section_checkpoints), the user's saved clarification answers
                    and the section's current content.
4. edit          -> the user writes the section text; it becomes the approved content.
5. approve       -> a proposal becomes the section's content; approving the BRD freezes a version.

Analogy: a ghost writer. The writer only sees the binder of approved answers, drafts each
chapter on a separate sheet (a proposal), and the author decides which sheet goes into the book
(project_artifact_sections). The writer never writes in the book directly.

Correctness:
- The agent never overwrites approved content. Its output is always a proposal.
- A newer proposal for a section supersedes the older open ones, so a section has at most one
  open proposal with content.
- Agent calls run in the background, outside any open transaction; each call is logged in
  agent_runs (brd_generate / brd_regenerate / brd_clarify). One BRD run per project at a time.
- A failed regenerate keeps the existing content: nothing is written when the agent fails.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy import func, select, true, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import api_error
from app.core.time import utc_now
from app.db.models import (
    Agent,
    AgentRun,
    ArtifactSection,
    ArtifactSectionCheckpoint,
    ArtifactSectionClarification,
    ArtifactSectionProposal,
    ArtifactType,
    ArtifactTypePillar,
    DiscoveryCheckpoint,
    DiscoveryPillar,
    Project,
    ProjectArtifact,
    ProjectArtifactSection,
    ProjectArtifactVersion,
    ProjectCheckpointAnswer,
)
from app.db.session import get_session_factory
from app.services import brd_agent_io as io
from app.services.agent_client import AgentError, call_brd_agent, call_with_retry

log = logging.getLogger(__name__)

ARTIFACT_CODE = "BRD"
BRD_AGENT_CODE = "BRD_AGENT"
RUN_GENERATE = "brd_generate"
RUN_REGENERATE = "brd_regenerate"
RUN_CLARIFY = "brd_clarify"
OPEN_PROPOSAL_STATUSES = ("PENDING", "NEEDS_CLARIFICATION")
# A run still "running" after this long is treated as dead (for example the server restarted).
# A generate run makes up to ~15 agent calls of several minutes each, so this is generous.
STALE_RUN_MINUTES = 60
# Calls per mode when the reply cannot be read.
PARSE_ATTEMPTS = 2
PREFETCH_WORKERS = 4
GENERIC_FAILURE = "The BRD could not be generated. Please try again."
# Automatic refreshes started back to back at most (answers approved while a run was busy).
MAX_REFRESH_CHAIN = 5


class BrdRunError(Exception):
    """A run ended without a usable result. The message is safe to show to the user."""


# ---------------------------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------------------------


def _owned_project(db: Session, owner_id: int, project_id: int) -> Project:
    project = db.scalar(select(Project).where(Project.id == project_id, Project.owner_id == owner_id))
    if project is None:
        raise api_error(404, "PROJECT_NOT_FOUND", "Project not found")
    return project


def _brd_type(db: Session) -> ArtifactType:
    artifact_type = db.scalar(select(ArtifactType).where(ArtifactType.code == ARTIFACT_CODE))
    if artifact_type is None:
        raise api_error(500, "BRD_NOT_CONFIGURED", "The BRD template is missing. Run the database migrations.")
    return artifact_type


def _template(db: Session, artifact_type_id: int) -> list[ArtifactSection]:
    return list(
        db.scalars(
            select(ArtifactSection)
            .where(ArtifactSection.artifact_type_id == artifact_type_id, ArtifactSection.is_active == true())
            .order_by(ArtifactSection.sort_order)
        )
    )


def _brd_agent_id(db: Session) -> int:
    agent_id = db.scalar(select(Agent.id).where(Agent.agent_code == BRD_AGENT_CODE))
    if agent_id is None:
        raise BrdRunError("The BRD agent is not configured. Run the database migrations.")
    return agent_id


def _find_brd(db: Session, project_id: int, artifact_type_id: int) -> ProjectArtifact | None:
    return db.scalar(
        select(ProjectArtifact).where(
            ProjectArtifact.project_id == project_id, ProjectArtifact.artifact_type_id == artifact_type_id
        )
    )


def _get_or_create_brd(db: Session, project_id: int, user_id: int) -> ProjectArtifact:
    """The project's BRD, with one section row per template section. Creates what is missing."""
    artifact_type = _brd_type(db)
    artifact = _find_brd(db, project_id, artifact_type.id)
    if artifact is None:
        artifact = ProjectArtifact(project_id=project_id, artifact_type_id=artifact_type.id, created_by=user_id)
        db.add(artifact)
        db.flush()
    existing = set(
        db.scalars(
            select(ProjectArtifactSection.artifact_section_id).where(
                ProjectArtifactSection.project_artifact_id == artifact.id
            )
        )
    )
    for section in _template(db, artifact_type.id):
        if section.id not in existing:
            db.add(ProjectArtifactSection(project_artifact_id=artifact.id, artifact_section_id=section.id))
    db.flush()
    return artifact


def _section_rows(db: Session, artifact_id: int) -> list[ProjectArtifactSection]:
    """The BRD's sections in template order, each with its template row loaded."""
    return list(
        db.scalars(
            select(ProjectArtifactSection)
            .join(ArtifactSection, ArtifactSection.id == ProjectArtifactSection.artifact_section_id)
            .where(ProjectArtifactSection.project_artifact_id == artifact_id, ArtifactSection.is_active == true())
            .order_by(ArtifactSection.sort_order)
        )
    )


def _section_by_key(db: Session, artifact_id: int, section_key: str) -> ProjectArtifactSection:
    for row in _section_rows(db, artifact_id):
        if row.section.section_key == section_key:
            return row
    raise api_error(404, "SECTION_NOT_FOUND", "BRD section not found")


def _feeding_checkpoint_ids(db: Session, artifact_section_id: int) -> set[int] | None:
    """Checkpoints that feed the section. None means every checkpoint (for example Assumptions)."""
    ids = set(
        db.scalars(
            select(ArtifactSectionCheckpoint.checkpoint_id).where(
                ArtifactSectionCheckpoint.artifact_section_id == artifact_section_id
            )
        )
    )
    return ids or None


def _brd_pillar_ids(db: Session) -> set[int]:
    """The pillars whose answers the BRD is written from (artifact_type_pillars). User Discovery today."""
    return set(
        db.scalars(
            select(ArtifactTypePillar.pillar_id)
            .join(ArtifactType, ArtifactType.id == ArtifactTypePillar.artifact_type_id)
            .where(ArtifactType.code == ARTIFACT_CODE)
        )
    )


def approved_answers(db: Session, project_id: int, checkpoint_ids: set[int] | None = None) -> list[dict]:
    """
    The project's APPROVED answers (approved_at is set and the answer is not empty) of the BRD's
    pillars, ordered by pillar and checkpoint. Limited to checkpoint_ids when given.
    """
    query = (
        select(
            DiscoveryCheckpoint.code,
            DiscoveryCheckpoint.name,
            DiscoveryPillar.name,
            DiscoveryCheckpoint.question,
            ProjectCheckpointAnswer.current_answer,
        )
        .join(DiscoveryCheckpoint, DiscoveryCheckpoint.id == ProjectCheckpointAnswer.checkpoint_id)
        .join(DiscoveryPillar, DiscoveryPillar.id == DiscoveryCheckpoint.pillar_id)
        .where(
            ProjectCheckpointAnswer.project_id == project_id,
            ProjectCheckpointAnswer.approved_at.is_not(None),
            ProjectCheckpointAnswer.current_answer.is_not(None),
            DiscoveryCheckpoint.pillar_id.in_(_brd_pillar_ids(db)),
        )
        .order_by(DiscoveryPillar.id, DiscoveryCheckpoint.sort_order, DiscoveryCheckpoint.code)
    )
    if checkpoint_ids is not None:
        query = query.where(ProjectCheckpointAnswer.checkpoint_id.in_(checkpoint_ids))
    return [
        {"code": code, "name": name, "pillar": pillar, "question": question, "answer": answer}
        for code, name, pillar, question, answer in db.execute(query).all()
        if answer and answer.strip()
    ]


def latest_approval(db: Session, project_id: int):
    """When the newest BRD input answer was approved (None when nothing is approved)."""
    return db.scalar(
        select(func.max(ProjectCheckpointAnswer.approved_at))
        .join(DiscoveryCheckpoint, DiscoveryCheckpoint.id == ProjectCheckpointAnswer.checkpoint_id)
        .where(
            ProjectCheckpointAnswer.project_id == project_id,
            ProjectCheckpointAnswer.current_answer.is_not(None),
            DiscoveryCheckpoint.pillar_id.in_(_brd_pillar_ids(db)),
        )
    )


def _answers_as_of(db: Session, artifact_id: int):
    """The newest approval the last successful generate run had read (None when there was none)."""
    payload = db.scalar(
        select(AgentRun.input_payload)
        .where(
            AgentRun.project_artifact_id == artifact_id,
            AgentRun.run_type == RUN_GENERATE,
            AgentRun.status == "succeeded",
        )
        .order_by(AgentRun.id.desc())
    )
    value = json.loads(payload or "{}").get("answers_as_of")
    return datetime.fromisoformat(value) if value else None


def _is_outdated(db: Session, project_id: int, artifact: ProjectArtifact | None) -> bool:
    newest = latest_approval(db, project_id)
    if newest is None:
        return False
    as_of = _answers_as_of(db, artifact.id) if artifact else None
    return as_of is None or newest > as_of


def _all_clarifications_text(db: Session, sections: list[ProjectArtifactSection]) -> str:
    """The user's saved clarification answers of every section, so a full regeneration keeps them."""
    blocks = []
    for section in sections:
        pairs = _clarification_pairs(db, section)
        if pairs:
            blocks.append(
                f"--- USER CLARIFICATIONS FOR SECTION {section.section.section_key} ({section.section.title}) ---\n"
                + io.format_clarifications(pairs)
            )
    return ("\n\nUSER CLARIFICATION ANSWERS\n\n" + "\n\n".join(blocks)) if blocks else ""


def _open_proposal(db: Session, section_id: int) -> ArtifactSectionProposal | None:
    return db.scalar(
        select(ArtifactSectionProposal)
        .where(
            ArtifactSectionProposal.project_artifact_section_id == section_id,
            ArtifactSectionProposal.status.in_(OPEN_PROPOSAL_STATUSES),
        )
        .order_by(ArtifactSectionProposal.id.desc())
    )


def _clarification_pairs(db: Session, section: ProjectArtifactSection) -> list[tuple[str, str]]:
    """
    The user's saved answers for the section. After the user edits the section, the edited text is
    the truth, so only answers given after that edit are reused (older ones may re-add removed facts).
    """
    query = select(ArtifactSectionClarification.question, ArtifactSectionClarification.answer).where(
        ArtifactSectionClarification.project_artifact_section_id == section.id
    )
    if section.source == "USER" and section.approved_at is not None:
        query = query.where(ArtifactSectionClarification.created_at > section.approved_at)
    return [(q, a) for q, a in db.execute(query.order_by(ArtifactSectionClarification.id)).all()]


def _fallback_questions(section: ArtifactSection) -> list[str]:
    try:
        questions = json.loads(section.fallback_questions or "[]")
    except ValueError:
        return []
    return [str(q) for q in questions if str(q).strip()][: io.MAX_QUESTIONS] if isinstance(questions, list) else []


# ---------------------------------------------------------------------------------------------
# Starting runs (request thread). Each returns the agent_run id; the route queues run_brd_job.
# ---------------------------------------------------------------------------------------------


def start_generate(db: Session, owner_id: int, project_id: int) -> int:
    _owned_project(db, owner_id, project_id)
    if not approved_answers(db, project_id):
        raise api_error(
            409, "NO_APPROVED_ANSWERS", "The BRD is written from approved checkpoint answers. None are approved yet."
        )
    artifact = _get_or_create_brd(db, project_id, owner_id)
    return _new_run(db, artifact, None, RUN_GENERATE, {"mode": io.MODE_GENERATE_ALL})


def start_regenerate(
    db: Session, owner_id: int, project_id: int, section_key: str, answers: list[dict] | None = None
) -> int:
    """Save the user's new clarification answers (if any), then queue a rewrite of one section."""
    _owned_project(db, owner_id, project_id)
    artifact = _get_or_create_brd(db, project_id, owner_id)
    section = _section_by_key(db, artifact.id, section_key)
    _ensure_no_running_run(db, artifact.id)

    answers = [a for a in (answers or []) if a["answer"].strip()]
    if answers:
        open_proposal = _open_proposal(db, section.id)
        for item in answers:
            db.add(
                ArtifactSectionClarification(
                    project_artifact_section_id=section.id,
                    proposal_id=open_proposal.id if open_proposal else None,
                    question=item["question"][:1000],
                    answer=item["answer"].strip(),
                    answered_by=owner_id,
                )
            )
        db.flush()

    has_answers = bool(approved_answers(db, project_id, _feeding_checkpoint_ids(db, section.artifact_section_id)))
    if not (has_answers or section.current_content or _clarification_pairs(db, section)):
        db.rollback()
        raise api_error(
            409,
            "NOTHING_TO_WRITE_FROM",
            "No approved answer feeds this section and it has no content or clarifications yet. Use Clarify first.",
        )
    return _new_run(db, artifact, section, RUN_REGENERATE, {"mode": io.MODE_REGENERATE_SECTION, "section": section_key})


def start_clarify(db: Session, owner_id: int, project_id: int, section_key: str) -> int:
    _owned_project(db, owner_id, project_id)
    artifact = _get_or_create_brd(db, project_id, owner_id)
    section = _section_by_key(db, artifact.id, section_key)
    return _new_run(db, artifact, section, RUN_CLARIFY, {"mode": io.MODE_CLARIFY_QUESTIONS, "section": section_key})


def _ensure_no_running_run(db: Session, artifact_id: int) -> None:
    cutoff = utc_now() - timedelta(minutes=STALE_RUN_MINUTES)
    running = db.scalar(
        select(AgentRun.id).where(
            AgentRun.project_artifact_id == artifact_id,
            AgentRun.status == "running",
            AgentRun.started_at > cutoff,
        )
    )
    if running is not None:
        raise api_error(409, "BRD_RUN_IN_PROGRESS", "The BRD agent is already working on this BRD. Please wait.")


def _new_run(
    db: Session,
    artifact: ProjectArtifact,
    section: ProjectArtifactSection | None,
    run_type: str,
    input_payload: dict,
) -> int:
    _close_stale_runs(db, artifact.id)
    _ensure_no_running_run(db, artifact.id)
    run = AgentRun(
        project_id=artifact.project_id,
        agent_id=_brd_agent_id(db),
        run_type=run_type,
        status="running",
        chunk_count=0,
        attempt_count=0,
        input_payload=json.dumps(input_payload),
        project_artifact_id=artifact.id,
        project_artifact_section_id=section.id if section else None,
    )
    db.add(run)
    try:
        db.commit()
    except IntegrityError:
        # ux_agent_runs_one_running_artifact: another request started a run a moment ago.
        db.rollback()
        raise api_error(409, "BRD_RUN_IN_PROGRESS", "The BRD agent is already working on this BRD. Please wait.") from None
    return run.id


def _close_stale_runs(db: Session, artifact_id: int) -> None:
    """Runs left "running" by a stopped server would block every new run; mark them failed."""
    db.execute(
        update(AgentRun)
        .where(
            AgentRun.project_artifact_id == artifact_id,
            AgentRun.status == "running",
            AgentRun.started_at <= utc_now() - timedelta(minutes=STALE_RUN_MINUTES),
        )
        .values(status="failed", completed_at=utc_now(), error_message="Stopped before it finished.")
    )


# ---------------------------------------------------------------------------------------------
# Background job
# ---------------------------------------------------------------------------------------------


def refresh_brd(project_id: int, _chain: int = 0) -> None:
    """
    Regenerate the project's BRD when an approved User Discovery answer is newer than what the BRD
    was last written from. Called in the background after an answer is approved. Never raises.

    When a BRD run is already busy, nothing starts now: that run checks again when it finishes.
    The BRD is created on the first approved answer if the project has none yet.
    """
    if not get_settings().brd_auto_refresh or _chain >= MAX_REFRESH_CHAIN:
        return
    try:
        with get_session_factory()() as db:
            project = db.get(Project, project_id)
            if project is None or not approved_answers(db, project_id):
                return
            artifact = _find_brd(db, project_id, _brd_type(db).id)
            if not _is_outdated(db, project_id, artifact):
                return
            artifact = _get_or_create_brd(db, project_id, project.owner_id)
            try:
                run_id = _new_run(db, artifact, None, RUN_GENERATE, {"mode": io.MODE_GENERATE_ALL, "trigger": "auto"})
            except HTTPException:
                db.rollback()  # a run is busy; it re-checks when it ends
                return
    except Exception:  # noqa: BLE001 - a refresh must never break the approval that triggered it
        log.exception("Could not start the BRD refresh for project %s", project_id)
        return
    log.info("BRD refresh started for project %s (run %s)", project_id, run_id)
    run_brd_job(run_id, _chain + 1)


def run_brd_job(agent_run_id: int, _chain: int = 0) -> None:
    """Run one queued BRD run. Never raises: a failure is recorded on the run."""
    project_id = None
    try:
        with get_session_factory()() as db:
            run = db.get(AgentRun, agent_run_id)
            if run is None or run.status != "running":
                return
            project_id = run.project_id
            handlers = {RUN_GENERATE: _run_generate, RUN_REGENERATE: _run_regenerate, RUN_CLARIFY: _run_clarify}
            handlers[run.run_type](db, run)
    except Exception as exc:  # noqa: BLE001 - recorded on the run, never lost
        _record_failure(agent_run_id, exc)
        return
    # Answers approved while this run was busy: write the BRD once more with them.
    refresh_brd(project_id, _chain)


def _call_and_parse(text_input: str, section_keys: list[str], mode: str, target: str) -> tuple[dict, int]:
    """One agent call (with the client's retry on timeouts/5xx), parsed. Returns (result, calls made)."""
    last_error: io.AgentReplyError | None = None
    for attempt in range(1, PARSE_ATTEMPTS + 1):
        raw = call_with_retry(lambda: call_brd_agent(text_input), f"BRD agent ({mode})")
        try:
            return io.normalize_agent_response(raw, section_keys, mode, target), attempt
        except io.AgentReplyError as exc:
            last_error = exc
            log.warning("BRD agent reply could not be read (%s, attempt %d/%d)", mode, attempt, PARSE_ATTEMPTS)
    raise last_error  # type: ignore[misc]


def _run_generate(db: Session, run: AgentRun) -> None:
    sections = _section_rows(db, run.project_artifact_id)
    keys = [s.section.section_key for s in sections]
    answers = approved_answers(db, run.project_id)
    if not answers:
        raise BrdRunError("No approved User Discovery answers yet.")
    as_of = latest_approval(db, run.project_id)
    source = io.build_source_text(answers) + _all_clarifications_text(db, sections)
    payload = json.loads(run.input_payload or "{}")
    payload.update(answers_as_of=as_of.isoformat() if as_of else None, checkpoint_codes=[a["code"] for a in answers])
    run.input_payload = json.dumps(payload)
    db.commit()  # release the connection while the agent works

    result, calls = _call_and_parse(io.build_agent_input(source, io.MODE_GENERATE_ALL), keys, io.MODE_GENERATE_ALL, "")
    calls += _prefetch_questions(source, result, keys)

    now = utc_now()
    agent_id = _brd_agent_id(db)
    for section in sections:
        item = result["sections"][section.section.section_key]
        if item["status"] == "insufficient" and not item["questions"]:
            item["questions"] = _fallback_questions(section.section)
        _save_proposal(db, run, section, item, agent_id, now)
    _mark_draft(db.get(ProjectArtifact, run.project_artifact_id), now)
    _succeed(run, result, calls, now)
    db.commit()


def _prefetch_questions(source: str, result: dict, keys: list[str]) -> int:
    """Up to 3 questions for every empty section that came back without any. Returns calls made."""
    missing = [k for k in keys if result["sections"][k]["status"] == "insufficient" and not result["sections"][k]["questions"]]
    if not missing:
        return 0

    def fetch(key: str) -> list[str]:
        try:
            text = io.build_agent_input(source, io.MODE_CLARIFY_QUESTIONS, key)
            reply, _ = _call_and_parse(text, keys, io.MODE_CLARIFY_QUESTIONS, key)
            return reply["questions"] or reply["sections"][key]["questions"]
        except Exception:  # noqa: BLE001 - a missing question list is not worth failing the BRD
            log.warning("Could not prefetch clarification questions for BRD section %s", key)
            return []

    with ThreadPoolExecutor(max_workers=PREFETCH_WORKERS) as pool:
        for key, questions in zip(missing, pool.map(fetch, missing)):
            result["sections"][key]["questions"] = questions
    return len(missing)


def _run_regenerate(db: Session, run: AgentRun) -> None:
    section = db.get(ProjectArtifactSection, run.project_artifact_section_id)
    key = section.section.section_key
    keys = [s.section.section_key for s in _section_rows(db, run.project_artifact_id)]
    source = io.build_source_text(
        approved_answers(db, run.project_id, _feeding_checkpoint_ids(db, section.artifact_section_id))
    )
    clarification = io.format_clarifications(_clarification_pairs(db, section))
    open_proposal = _open_proposal(db, section.id)
    current = section.current_content or (open_proposal.proposed_content if open_proposal else None) or ""
    has_facts = bool(clarification or current)
    if not clarification and current:
        clarification = io.USER_CONTENT_PREFIX + current
    db.commit()

    calls, result, item = 0, None, None
    for prefix in io.REGENERATE_PREFIXES[: 3 if has_facts else 1]:
        text = io.build_agent_input(source, io.MODE_REGENERATE_SECTION, key, prefix + clarification, current)
        result, used = _call_and_parse(text, keys, io.MODE_REGENERATE_SECTION, key)
        calls += used
        item = result["sections"][key]
        if item["status"] == "complete" or not has_facts:
            break

    if item["status"] == "skipped":
        raise BrdRunError("The BRD agent skipped this section. Check the agent's control-block handling.")
    if item["status"] != "complete" and has_facts:
        # Never replace good content with an empty result.
        raise BrdRunError("The agent could not produce a new version this time. The existing content was kept.")
    if item["status"] == "insufficient" and not item["questions"]:
        item["questions"] = _fallback_questions(section.section)

    now = utc_now()
    _save_proposal(db, run, section, item, _brd_agent_id(db), now)
    _mark_draft(db.get(ProjectArtifact, run.project_artifact_id), now)
    _succeed(run, result, calls, now)
    db.commit()


def _run_clarify(db: Session, run: AgentRun) -> None:
    section = db.get(ProjectArtifactSection, run.project_artifact_section_id)
    key = section.section.section_key
    keys = [s.section.section_key for s in _section_rows(db, run.project_artifact_id)]
    source = io.build_source_text(
        approved_answers(db, run.project_id, _feeding_checkpoint_ids(db, section.artifact_section_id))
    )
    current = section.current_content or ""
    fallback = _fallback_questions(section.section)
    db.commit()

    text = io.build_agent_input(source, io.MODE_CLARIFY_QUESTIONS, key, "", current)
    result, calls = _call_and_parse(text, keys, io.MODE_CLARIFY_QUESTIONS, key)
    questions = result["questions"] or result["sections"][key]["questions"] or fallback
    if not questions:
        raise BrdRunError("The BRD agent returned no clarification questions for this section.")

    now = utc_now()
    item = {"status": "insufficient", "content": "", "message": "", "questions": questions}
    _save_proposal(db, run, section, item, _brd_agent_id(db), now, questions_only=True)
    _succeed(run, result, calls, now)
    db.commit()


def _save_proposal(
    db: Session,
    run: AgentRun,
    section: ProjectArtifactSection,
    item: dict,
    agent_id: int,
    now,
    questions_only: bool = False,
) -> ArtifactSectionProposal | None:
    """
    complete -> PENDING proposal with content; insufficient -> NEEDS_CLARIFICATION with the reason
    and questions; skipped -> nothing. A new content proposal supersedes every open proposal of the
    section; a questions-only proposal (Clarify) supersedes only older question lists.
    """
    if item["status"] == "skipped":
        return None
    is_content = item["status"] == "complete"
    superseded = ("PENDING", "NEEDS_CLARIFICATION") if not questions_only else ("NEEDS_CLARIFICATION",)
    for old in db.scalars(
        select(ArtifactSectionProposal).where(
            ArtifactSectionProposal.project_artifact_section_id == section.id,
            ArtifactSectionProposal.status.in_(superseded),
        )
    ):
        old.status = "SUPERSEDED"

    proposal = ArtifactSectionProposal(
        project_artifact_section_id=section.id,
        proposed_content=item["content"] if is_content else None,
        status="PENDING" if is_content else "NEEDS_CLARIFICATION",
        missing_reason=None if is_content else (item["message"][:1000] or None),
        clarification_questions=None if is_content else json.dumps(item["questions"], ensure_ascii=False),
        generated_by_agent_id=agent_id,
        agent_run_id=run.id,
    )
    db.add(proposal)

    if is_content:
        section.status = "PENDING_REVIEW"
    elif questions_only and section.status == "PENDING_REVIEW":
        pass  # Clarify only adds questions; the draft waiting for review stays open.
    else:
        # Any earlier draft was just superseded, so the status follows what the section holds now:
        # its approved content if it has some, otherwise the open questions.
        section.status = "APPROVED" if section.current_content else "NEEDS_CLARIFICATION"
    section.updated_at = now
    db.flush()
    return proposal


def _mark_draft(artifact: ProjectArtifact, now) -> None:
    artifact.status = "DRAFT"
    artifact.updated_at = now


def _succeed(run: AgentRun, result: dict | None, calls: int, now) -> None:
    run.status = "succeeded"
    run.attempt_count = calls
    run.raw_output = json.dumps(result, ensure_ascii=False) if result is not None else None
    run.completed_at = now


def _record_failure(agent_run_id: int, exc: Exception) -> None:
    if isinstance(exc, (BrdRunError, AgentError)):
        message = str(exc)
        log.warning("BRD run %s failed: %s", agent_run_id, message)
    elif isinstance(exc, io.AgentReplyError):
        message = "The BRD agent's reply could not be read. Please try again."
        log.warning("BRD run %s failed: %s", agent_run_id, exc)
    else:
        message = GENERIC_FAILURE
        log.exception("BRD run %s failed", agent_run_id)
    try:
        with get_session_factory()() as db:
            run = db.get(AgentRun, agent_run_id)
            if run is not None:
                run.status = "failed"
                run.error_message = message[:1000]
                run.completed_at = utc_now()
                db.commit()
    except Exception:  # noqa: BLE001
        log.exception("Could not record the failure of BRD run %s", agent_run_id)


# ---------------------------------------------------------------------------------------------
# User actions (request thread)
# ---------------------------------------------------------------------------------------------


def get_brd(db: Session, owner_id: int, project_id: int) -> dict:
    """The BRD with every section, its open proposal and saved clarifications, and the latest run."""
    _owned_project(db, owner_id, project_id)
    artifact_type = _brd_type(db)
    artifact = _find_brd(db, project_id, artifact_type.id)
    feeds = _feeds_by_section(db, artifact_type.id)
    approved_count = len(approved_answers(db, project_id))

    if artifact is None:
        return {
            "project_id": project_id,
            "status": "NOT_STARTED",
            "current_version": 0,
            "approved_answer_count": approved_count,
            "is_outdated": _is_outdated(db, project_id, None),
            "answers_as_of": None,
            "sections": [
                _section_dict(None, template, feeds.get(template.id, []), None, []) for template in _template(db, artifact_type.id)
            ],
            "latest_run": None,
        }

    sections = []
    for row in _section_rows(db, artifact.id):
        clarifications = list(
            db.scalars(
                select(ArtifactSectionClarification)
                .where(ArtifactSectionClarification.project_artifact_section_id == row.id)
                .order_by(ArtifactSectionClarification.id)
            )
        )
        sections.append(
            _section_dict(row, row.section, feeds.get(row.artifact_section_id, []), _open_proposal(db, row.id), clarifications)
        )
    latest = db.scalar(
        select(AgentRun).where(AgentRun.project_artifact_id == artifact.id).order_by(AgentRun.id.desc())
    )
    return {
        "project_id": project_id,
        "status": artifact.status,
        "current_version": artifact.current_version,
        "approved_answer_count": approved_count,
        "is_outdated": _is_outdated(db, project_id, artifact),
        "answers_as_of": _answers_as_of(db, artifact.id),
        "sections": sections,
        "latest_run": _run_dict(db, latest) if latest else None,
    }


def get_run(db: Session, owner_id: int, project_id: int, agent_run_id: int) -> dict:
    _owned_project(db, owner_id, project_id)
    run = db.scalar(
        select(AgentRun).where(
            AgentRun.id == agent_run_id,
            AgentRun.project_id == project_id,
            AgentRun.run_type.in_((RUN_GENERATE, RUN_REGENERATE, RUN_CLARIFY)),
        )
    )
    if run is None:
        raise api_error(404, "RUN_NOT_FOUND", "BRD run not found")
    return _run_dict(db, run)


def edit_section(db: Session, owner_id: int, project_id: int, section_key: str, content: str) -> dict:
    """The user's own text becomes the approved content of the section."""
    _owned_project(db, owner_id, project_id)
    content = io.clean_text(content)
    if not content:
        raise api_error(422, "EMPTY_CONTENT", "Section content cannot be empty")
    artifact = _get_or_create_brd(db, project_id, owner_id)
    section = _section_by_key(db, artifact.id, section_key)
    now = utc_now()
    for old in db.scalars(
        select(ArtifactSectionProposal).where(
            ArtifactSectionProposal.project_artifact_section_id == section.id,
            ArtifactSectionProposal.status.in_(OPEN_PROPOSAL_STATUSES),
        )
    ):
        old.status = "SUPERSEDED"
    _approve_content(section, content, "USER", owner_id, now)
    _mark_draft(artifact, now)
    db.commit()
    return _section_after_change(db, section)


def approve_proposal(db: Session, owner_id: int, project_id: int, proposal_id: int) -> dict:
    proposal, section, artifact = _owned_proposal(db, owner_id, project_id, proposal_id)
    if proposal.status != "PENDING" or not proposal.proposed_content:
        raise api_error(409, "PROPOSAL_NOT_PENDING", "Only a pending proposal with content can be approved")
    now = utc_now()
    proposal.status = "APPROVED"
    proposal.reviewed_by = owner_id
    proposal.reviewed_at = now
    _approve_content(section, proposal.proposed_content, "AGENT", owner_id, now)
    _mark_draft(artifact, now)
    db.commit()
    return _section_after_change(db, section)


def reject_proposal(db: Session, owner_id: int, project_id: int, proposal_id: int) -> dict:
    proposal, section, artifact = _owned_proposal(db, owner_id, project_id, proposal_id)
    if proposal.status not in OPEN_PROPOSAL_STATUSES:
        raise api_error(409, "PROPOSAL_NOT_OPEN", "Only an open proposal can be rejected")
    now = utc_now()
    proposal.status = "REJECTED"
    proposal.reviewed_by = owner_id
    proposal.reviewed_at = now
    section.status = "APPROVED" if section.current_content else "NOT_STARTED"
    section.updated_at = now
    db.commit()
    return _section_after_change(db, section)


def approve_brd(db: Session, owner_id: int, project_id: int) -> dict:
    """Freeze the current content of every section as the next version."""
    _owned_project(db, owner_id, project_id)
    artifact = _find_brd(db, project_id, _brd_type(db).id)
    if artifact is None:
        raise api_error(404, "BRD_NOT_FOUND", "This project has no BRD yet")
    rows = _section_rows(db, artifact.id)
    if not any(row.status == "APPROVED" and row.current_content for row in rows):
        raise api_error(409, "NOTHING_APPROVED", "Approve at least one section before approving the BRD")
    now = utc_now()
    snapshot = [
        {
            "section_key": row.section.section_key,
            "title": row.section.title,
            "sort_order": row.section.sort_order,
            "status": row.status,
            "content": row.current_content,
        }
        for row in rows
    ]
    version_number = artifact.current_version + 1
    db.add(
        ProjectArtifactVersion(
            project_artifact_id=artifact.id,
            version_number=version_number,
            snapshot=json.dumps(snapshot, ensure_ascii=False),
            approved_by=owner_id,
            approved_at=now,
        )
    )
    artifact.current_version = version_number
    artifact.status = "APPROVED"
    artifact.approved_by = owner_id
    artifact.approved_at = now
    artifact.updated_at = now
    db.commit()
    return {"version_number": version_number, "approved_at": now}


def list_versions(db: Session, owner_id: int, project_id: int) -> list[dict]:
    _owned_project(db, owner_id, project_id)
    artifact = _find_brd(db, project_id, _brd_type(db).id)
    if artifact is None:
        return []
    rows = db.scalars(
        select(ProjectArtifactVersion)
        .where(ProjectArtifactVersion.project_artifact_id == artifact.id)
        .order_by(ProjectArtifactVersion.version_number.desc())
    )
    return [{"version_number": v.version_number, "approved_by": v.approved_by, "approved_at": v.approved_at} for v in rows]


def get_version(db: Session, owner_id: int, project_id: int, version_number: int) -> dict:
    _owned_project(db, owner_id, project_id)
    artifact = _find_brd(db, project_id, _brd_type(db).id)
    version = None
    if artifact is not None:
        version = db.scalar(
            select(ProjectArtifactVersion).where(
                ProjectArtifactVersion.project_artifact_id == artifact.id,
                ProjectArtifactVersion.version_number == version_number,
            )
        )
    if version is None:
        raise api_error(404, "VERSION_NOT_FOUND", "BRD version not found")
    return {
        "version_number": version.version_number,
        "approved_by": version.approved_by,
        "approved_at": version.approved_at,
        "sections": json.loads(version.snapshot),
    }


# ---------------------------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------------------------


def _approve_content(section: ProjectArtifactSection, content: str, source: str, user_id: int, now) -> None:
    section.current_content = content
    section.source = source
    section.status = "APPROVED"
    section.approved_by = user_id
    section.approved_at = now
    section.updated_at = now


def _owned_proposal(
    db: Session, owner_id: int, project_id: int, proposal_id: int
) -> tuple[ArtifactSectionProposal, ProjectArtifactSection, ProjectArtifact]:
    _owned_project(db, owner_id, project_id)
    row = db.execute(
        select(ArtifactSectionProposal, ProjectArtifactSection, ProjectArtifact)
        .join(ProjectArtifactSection, ProjectArtifactSection.id == ArtifactSectionProposal.project_artifact_section_id)
        .join(ProjectArtifact, ProjectArtifact.id == ProjectArtifactSection.project_artifact_id)
        .where(ArtifactSectionProposal.id == proposal_id, ProjectArtifact.project_id == project_id)
    ).first()
    if row is None:
        raise api_error(404, "PROPOSAL_NOT_FOUND", "Proposal not found")
    return row[0], row[1], row[2]


def _feeds_by_section(db: Session, artifact_type_id: int) -> dict[int, list[str]]:
    feeds: dict[int, list[str]] = {}
    rows = db.execute(
        select(ArtifactSectionCheckpoint.artifact_section_id, DiscoveryCheckpoint.code)
        .join(DiscoveryCheckpoint, DiscoveryCheckpoint.id == ArtifactSectionCheckpoint.checkpoint_id)
        .join(ArtifactSection, ArtifactSection.id == ArtifactSectionCheckpoint.artifact_section_id)
        .where(ArtifactSection.artifact_type_id == artifact_type_id)
        .order_by(DiscoveryCheckpoint.code)
    ).all()
    for section_id, code in rows:
        feeds.setdefault(section_id, []).append(code)
    return feeds


def _section_after_change(db: Session, section: ProjectArtifactSection) -> dict:
    artifact_type_id = section.section.artifact_type_id
    clarifications = list(
        db.scalars(
            select(ArtifactSectionClarification)
            .where(ArtifactSectionClarification.project_artifact_section_id == section.id)
            .order_by(ArtifactSectionClarification.id)
        )
    )
    return _section_dict(
        section,
        section.section,
        _feeds_by_section(db, artifact_type_id).get(section.artifact_section_id, []),
        _open_proposal(db, section.id),
        clarifications,
    )


def _section_dict(
    row: ProjectArtifactSection | None,
    template: ArtifactSection,
    fed_by: list[str],
    proposal: ArtifactSectionProposal | None,
    clarifications: list[ArtifactSectionClarification],
) -> dict:
    return {
        "section_key": template.section_key,
        "title": template.title,
        "sort_order": template.sort_order,
        "fed_by_checkpoints": fed_by,
        "status": row.status if row else "NOT_STARTED",
        "content": row.current_content if row else None,
        "source": row.source if row else None,
        "approved_at": row.approved_at if row else None,
        "open_proposal": (
            {
                "id": proposal.id,
                "status": proposal.status,
                "content": proposal.proposed_content,
                "missing_reason": proposal.missing_reason,
                "questions": json.loads(proposal.clarification_questions or "[]"),
                "created_at": proposal.created_at,
            }
            if proposal
            else None
        ),
        "clarifications": [
            {"id": c.id, "question": c.question, "answer": c.answer, "created_at": c.created_at} for c in clarifications
        ],
    }


def _run_dict(db: Session, run: AgentRun) -> dict:
    section_key = None
    if run.project_artifact_section_id:
        section = db.get(ProjectArtifactSection, run.project_artifact_section_id)
        section_key = section.section.section_key if section else None
    return {
        "id": run.id,
        "run_type": run.run_type,
        "status": run.status,
        "section_key": section_key,
        "error_message": run.error_message,
        "started_at": run.started_at,
        "completed_at": run.completed_at,
    }
