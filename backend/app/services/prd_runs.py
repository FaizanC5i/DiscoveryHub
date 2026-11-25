"""
The PRD's agent runs: generate (also Refresh), regenerate and clarify.

Everything else about the PRD is the BRD code with code="PRD" (brd_service): the same tables,
proposals, clarifications, versions and screens. Only the agent differs: the PRD Generation Agent
takes one JSON request (prd_agent_io.build_payload) and answers with a sections array.

Input: the project's APPROVED answers of the PRD's pillars (artifact_type_pillars: User + Tech).
User answers go in approved_user_discovery, Tech answers in prd_checkpoints.

Flow (same as the PRD agent builder's stand-alone app):
1. generate    -> the 25 sections are sent 3 per call (prd_batch_size), a few calls at a time
                  (prd_parallel_calls). A section the agent leaves out is asked for again on its own.
                  A section can come back with text, with questions, or with both.
2. clarify     -> our Clarify button: the agent is asked for 3 questions for one section.
3. regenerate  -> with new clarification answers: action "clarify" (update the section with them);
                  without: action "regenerate" (rewrite the section in better PRD language).

Correctness (as for the BRD):
- Output is always a proposal; approved content is never overwritten.
- A section that already has text keeps it when the agent sends only questions.
- A failed or empty regenerate keeps the existing content.
"""

import json
import logging
from concurrent.futures import ThreadPoolExecutor

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.time import utc_now
from app.db.models import AgentRun, ProjectArtifact, ProjectArtifactSection
from app.services import agent_client, artifact_readiness
from app.services import brd_service as brd
from app.services import prd_agent_io as prd_io
from app.services.agent_client import call_with_retry

log = logging.getLogger(__name__)

CODE = "PRD"
PARSE_ATTEMPTS = 2


# ---------------------------------------------------------------------------------------------
# Building the request
# ---------------------------------------------------------------------------------------------


def _definition(section: ProjectArtifactSection) -> dict:
    t = section.section
    return prd_io.section_definition(t.sort_order, t.section_key, t.title, t.prompt)


def _sources(db: Session, project_id: int, checkpoint_ids: set[int] | None = None, first: set[str] | None = None):
    """(all approved answers, User answers, Tech answers). Codes in `first` are listed first."""
    answers = brd.approved_answers(db, project_id, checkpoint_ids, code=CODE)
    if first:
        answers = sorted(answers, key=lambda a: a["code"] not in first)  # stable: keeps the order otherwise
    user = [a for a in answers if a["pillar_code"] == "USER"]
    tech = [a for a in answers if a["pillar_code"] != "USER"]
    return answers, prd_io.user_answers(user), prd_io.tech_answers(tech)


def _existing(db: Session, sections: list[ProjectArtifactSection], text: dict[int, str]) -> list[dict]:
    """What each section holds now (text on screen and the user's saved clarification answers)."""
    out = []
    for s in sections:
        pairs = brd._clarification_pairs(db, s)  # noqa: SLF001
        out.append({
            "section_id": s.section.sort_order,
            "current_answer": text.get(s.id, ""),
            "is_approved": s.status == "APPROVED" and bool(s.current_content),
            "missing_information": [],
            "clarification_history": _entries(s, pairs),
        })
    return out


def _entries(section: ProjectArtifactSection, pairs: list[tuple[str, str]]) -> list[dict]:
    return [{"id": f"{section.section.sort_order}-{i}", "question": q, "answer": a} for i, (q, a) in enumerate(pairs, 1)]


def _settings(db: Session, run: AgentRun) -> dict:
    artifact = db.get(ProjectArtifact, run.project_artifact_id)
    return {"title": artifact.title or "", "audience": artifact.audience or "", "scope": artifact.scope or ""}


def _call(payload: dict, numbers: dict[int, str]) -> tuple[dict, int]:
    """One agent call (the client retries timeouts / 5xx), read. Returns (sections by key, calls made)."""
    last: prd_io.PrdReplyError | None = None
    for attempt in range(1, PARSE_ATTEMPTS + 1):
        raw = call_with_retry(lambda: agent_client.call_prd_agent(payload), f"PRD agent ({payload['action']})")
        try:
            return prd_io.normalize_reply(raw, numbers), attempt
        except prd_io.PrdReplyError as exc:
            last = exc
            log.warning("PRD agent reply could not be read (%s, attempt %d/%d)", payload["action"], attempt, PARSE_ATTEMPTS)
    raise last  # type: ignore[misc]


# ---------------------------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------------------------


def run_generate(db: Session, run: AgentRun) -> None:
    sections = brd._section_rows(db, run.project_artifact_id)  # noqa: SLF001
    payload_in = json.loads(run.input_payload or "{}")
    is_refresh = payload_in.get("trigger") == brd.TRIGGER_REFRESH

    new_codes: list[str] = []
    if is_refresh:
        # Answers approved since the last generation go first and take priority.
        previous = brd._answers_as_of(db, run.project_artifact_id)  # noqa: SLF001
        if previous is not None:
            new_codes = [
                a["code"] for a in brd.approved_answers(db, run.project_id, code=CODE)
                if a["approved_at"] and a["approved_at"] > previous
            ]
    answers, user, tech = _sources(db, run.project_id, first=set(new_codes))
    if not answers:
        raise brd.BrdRunError("No approved User or Tech Discovery answers yet.")

    text = brd._current_brd_text(db, sections)  # noqa: SLF001 - drafts on screen, else current content
    existing = {e["section_id"]: e for e in _existing(db, sections, text)}
    definitions = [_definition(s) for s in sections]
    settings = _settings(db, run)
    as_of = brd.latest_approval(db, run.project_id, CODE)
    payload_in.update(
        answers_as_of=as_of.isoformat() if as_of else None,
        checkpoint_codes=[a["code"] for a in answers],
        new_checkpoint_codes=new_codes,
        snapshot=artifact_readiness.snapshot(db, run.project_id, brd._brd_pillar_ids(db, CODE)),  # noqa: SLF001
    )
    run.input_payload = json.dumps(payload_in)
    project_id, run_id = run.project_id, run.id
    db.commit()  # release the connection while the agent works

    config = get_settings()
    size = max(1, config.prd_batch_size)
    batches = [definitions[i:i + size] for i in range(0, len(definitions), size)]

    def write(batch: list[dict]) -> tuple[dict, int, Exception | None]:
        def ask(defs: list[dict]) -> tuple[dict, int]:
            payload = prd_io.build_payload(
                prd_io.ACTION_GENERATE, defs, user, tech, [existing[d["id"]] for d in defs],
                project_id=project_id, run_id=run_id, settings=settings, new_answer_codes=new_codes,
            )
            return _call(payload, {d["id"]: d["key"] for d in defs})

        try:
            result, calls = ask(batch)
        except Exception as exc:  # noqa: BLE001 - one failed batch must not lose the others
            log.warning("PRD batch %s failed: %s", [d["id"] for d in batch], exc)
            return {}, 0, exc
        for d in batch:  # a section left out of a batch is asked for on its own
            if d["key"] not in result:
                try:
                    single, used = ask([d])
                    result.update(single)
                    calls += used
                except Exception as exc:  # noqa: BLE001
                    log.warning("PRD section %s retry failed: %s", d["id"], exc)
        return result, calls, None

    results: dict[str, dict] = {}
    calls, errors = 0, []
    with ThreadPoolExecutor(max_workers=max(1, config.prd_parallel_calls)) as pool:
        for result, used, error in pool.map(write, batches):
            results.update(result)
            calls += used
            if error is not None:
                errors.append(error)
    if not results:
        raise errors[0] if errors else brd.BrdRunError("The PRD agent returned no sections.")

    now = utc_now()
    agent_id = brd._brd_agent_id(db, CODE)  # noqa: SLF001
    run = db.get(AgentRun, run_id)
    for section in sections:
        item = results.get(section.section.section_key)
        if item is None:
            continue  # not written this time: the section keeps what it has
        _save(db, run, section, item, agent_id, now, keep_text=section.id in text)
    brd._mark_draft(db.get(ProjectArtifact, run.project_artifact_id), now)  # noqa: SLF001
    brd._succeed(run, {"sections": results}, calls, now)  # noqa: SLF001
    missing = len(sections) - sum(1 for s in sections if s.section.section_key in results)
    if missing:
        run.error_message = f"{missing} of {len(sections)} sections could not be written this time. Use Refresh to try again."
    db.commit()


def _save(db: Session, run: AgentRun, section: ProjectArtifactSection, item: dict, agent_id: int, now,
          keep_text: bool, with_questions: bool = True) -> None:
    """Text -> a draft to review; questions -> the section's open questions (both can come together)."""
    if item["status"] == "complete":
        brd._save_proposal(db, run, section, item, agent_id, now)  # noqa: SLF001
        if with_questions and item["questions"]:
            brd._save_proposal(db, run, section, _questions(item, item["questions"]), agent_id, now, questions_only=True)  # noqa: SLF001
        return
    questions = item["questions"] or brd._fallback_questions(section.section)  # noqa: SLF001
    brd._save_proposal(db, run, section, _questions(item, questions), agent_id, now, questions_only=keep_text)  # noqa: SLF001


def _questions(item: dict, questions: list[str]) -> dict:
    return {"status": "insufficient", "content": "", "message": item["message"], "questions": questions}


def _one_section_request(db: Session, run: AgentRun):
    """(section, its definition, user answers, tech answers, its text now, saved clarification pairs)."""
    section = db.get(ProjectArtifactSection, run.project_artifact_section_id)
    _, user, tech = _sources(db, run.project_id, brd._feeding_checkpoint_ids(db, section.artifact_section_id))  # noqa: SLF001
    current = brd._current_brd_text(db, [section]).get(section.id, "")  # noqa: SLF001
    pairs = brd._clarification_pairs(db, section)  # noqa: SLF001
    return section, _definition(section), user, tech, current, pairs


def run_regenerate(db: Session, run: AgentRun) -> None:
    section, definition, user, tech, current, pairs = _one_section_request(db, run)
    new_answers = bool(json.loads(run.input_payload or "{}").get("new_answers"))
    action = prd_io.ACTION_CLARIFY if new_answers and pairs else prd_io.ACTION_REGENERATE
    payload = prd_io.build_payload(
        action, [definition], user, tech, _existing(db, [section], {section.id: current}),
        project_id=run.project_id, run_id=run.id, clarifications=_entries(section, pairs),
        target_section_id=definition["id"], settings=_settings(db, run),
    )
    run_id = run.id
    db.commit()

    result, calls = _call(payload, {definition["id"]: definition["key"]})
    item = result.get(definition["key"])
    if item is None:
        raise brd.BrdRunError("The PRD agent did not return this section. The existing content was kept.")
    if item["status"] != "complete" and (current or pairs):
        raise brd.BrdRunError("The agent could not produce a new version this time. The existing content was kept.")

    now = utc_now()
    run = db.get(AgentRun, run_id)
    # After the user answered the questions, no new round of questions (as in the PRD app).
    _save(db, run, section, item, brd._brd_agent_id(db, CODE), now, keep_text=False,  # noqa: SLF001
          with_questions=action == prd_io.ACTION_REGENERATE)
    brd._mark_draft(db.get(ProjectArtifact, run.project_artifact_id), now)  # noqa: SLF001
    brd._succeed(run, result, calls, now)  # noqa: SLF001
    db.commit()


def run_clarify(db: Session, run: AgentRun) -> None:
    section, definition, user, tech, current, _ = _one_section_request(db, run)
    payload = prd_io.build_payload(
        prd_io.ACTION_GENERATE, [definition], user, tech, _existing(db, [section], {section.id: current}),
        project_id=run.project_id, run_id=run.id, target_section_id=definition["id"],
        settings=_settings(db, run), ask_questions=True,
    )
    fallback = brd._fallback_questions(section.section)  # noqa: SLF001
    run_id = run.id
    db.commit()

    result, calls = _call(payload, {definition["id"]: definition["key"]})
    item = result.get(definition["key"]) or {"status": "insufficient", "content": "", "message": "", "questions": []}
    questions = item["questions"] or fallback
    if not questions:
        raise brd.BrdRunError("The PRD agent returned no clarification questions for this section.")

    now = utc_now()
    run = db.get(AgentRun, run_id)
    brd._save_proposal(db, run, section, _questions(item, questions), brd._brd_agent_id(db, CODE), now,  # noqa: SLF001
                       questions_only=True)
    brd._succeed(run, result, calls, now)  # noqa: SLF001
    db.commit()
