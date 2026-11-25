"""
What we send to the PRD Generation Agent and how we read its reply. Pure functions: no database,
no network.

The format is the one the PRD agent's builder defined (their stand-alone PRD app): the text
"PRD_REQUEST", a new line, then one JSON object (agent_client.call_prd_agent adds the prefix):

    action                   generate | clarify | regenerate
    revision_instruction     what to do in this action
    instructions             the evidence rules (approved answers only, 3 questions when missing)
    approved_user_discovery  [{checkpoint_code, name, approved_answer, evidence}]          User pillar
    prd_checkpoints          [{id, code, name, question, description, is_approved, approved_answer}]  Tech pillar
    prd_sections             the sections to write: [{id 1-25, code PRDS01.., title, key_contents, ...}]
    existing_sections        [{section_id, current_answer, is_approved, missing_information, clarification_history}]
    clarifications           the user's new answers for the target section [{id, question, answer}]
    target_section_id        the section for clarify / regenerate (None for generate)
Added by Discovery Hub (the agent may ignore them): document_settings, new_or_updated_answers.

The reply: {"sections": [{section_id, proposed_answer, missing_information, clarification_questions,
mapped_source_checkpoints, evidence, completion_score, is_completed}]}, possibly wrapped by Agent5i.
normalize_reply() turns it into the per-section shape the BRD code already stores:
    {section_key: {"status": complete|insufficient, "content", "message", "questions"}}
"""

import json
from typing import Any

from app.services.agent_reply import find_json_objects

ACTION_GENERATE = "generate"
ACTION_CLARIFY = "clarify"
ACTION_REGENERATE = "regenerate"
MAX_QUESTIONS = 3

INSTRUCTIONS = (
    "Map APPROVED source answer content to each requested PRD section. "
    "For a section with no relevant approved evidence, return proposed_answer empty, "
    "mapped_source_checkpoints empty and exactly 3 clarification questions. "
    "For a partially evidenced section, provide only supported content plus missing information "
    "and exactly 3 questions. For clarify or regenerate after user clarification was submitted, "
    "use the saved clarification answers to update the draft and return no NEW clarification questions. "
    "Incorporate user clarifications during clarification or regeneration. "
    "Return JSON with sections array. Do not invent project facts."
)
REVISION_INSTRUCTIONS = {
    ACTION_GENERATE: "GENERATE every requested section, even when no evidence matches.",
    ACTION_CLARIFY: (
        "UPDATE ONLY THE TARGET SECTION using the new clarification answers "
        "and the previous draft. Return one section inside sections array; "
        "do not ask another clarification round."
    ),
    ACTION_REGENERATE: (
        "REGENERATE ONLY THE TARGET SECTION. Rewrite its previous proposed_answer "
        "in clearer, more polished professional PRD language. Use the supplied "
        "approved source evidence and any saved clarification answers. Preserve "
        "confirmed facts and meaningful requirements, but improve organization "
        "and phrasing. Do NOT require user feedback or create new questions after "
        "clarifications have been submitted. Return ONE section as valid JSON "
        "with the outer sections array and the exact target_section_id."
    ),
}
REFRESH_INSTRUCTION = (
    " REFRESH: existing_sections hold the PRD written earlier from older answers. The answers listed in "
    "new_or_updated_answers were approved since then and take the HIGHEST PRIORITY: update each section with "
    "them, keep what is still true, add what is new and remove what they contradict."
)
QUESTIONS_INSTRUCTION = (
    "The user asked for clarification questions for the TARGET SECTION only. Return that one section with "
    "exactly 3 clarification_questions about the information still missing from it, and its current draft, "
    "unchanged, as proposed_answer."
)


class PrdReplyError(ValueError):
    """The reply did not contain the PRD sections array."""


def section_definition(sort_order: int, section_key: str, title: str, prompt: str | None) -> dict:
    """One prd_sections entry. prompt is the JSON definition stored by migration 019."""
    try:
        extra = json.loads(prompt or "{}")
    except ValueError:
        extra = {"description": prompt}
    if not isinstance(extra, dict):
        extra = {"description": str(extra)}
    return {
        "id": sort_order,
        "code": f"PRDS{sort_order:02d}",
        "key": section_key,
        "title": title,
        "name": title,
        "description": extra.get("description") or "",
        "key_contents": extra.get("key_contents") or "",
        "required_details": extra.get("required_details") or [],
        "expected_format": extra.get("expected_format") or "",
        "question": extra.get("question") or "",
    }


def user_answers(answers: list[dict]) -> list[dict]:
    """Approved User Discovery answers, in the agent's approved_user_discovery shape."""
    return [
        {
            "checkpoint_code": a["code"],
            "name": a["name"],
            "question": a["question"],
            "approved_answer": (a["answer"] or "").strip(),
            "evidence": [],
        }
        for a in answers
    ]


def tech_answers(answers: list[dict]) -> list[dict]:
    """Approved Tech Discovery answers, in the agent's prd_checkpoints shape (approved ones only)."""
    return [
        {
            "id": a.get("checkpoint_id"),
            "code": a["code"],
            "name": a["name"],
            "question": a["question"],
            "description": a.get("description") or "",
            "is_approved": True,
            "approved_answer": (a["answer"] or "").strip(),
        }
        for a in answers
    ]


def build_payload(
    action: str,
    sections: list[dict],
    user: list[dict],
    tech: list[dict],
    existing: list[dict],
    *,
    project_id: int,
    run_id: int,
    clarifications: list[dict] | None = None,
    target_section_id: int | None = None,
    settings: dict | None = None,
    new_answer_codes: list[str] | None = None,
    ask_questions: bool = False,
) -> dict:
    revision = REVISION_INSTRUCTIONS[action]
    if new_answer_codes:
        revision += REFRESH_INSTRUCTION
    if ask_questions:
        revision = QUESTIONS_INSTRUCTION
    payload = {
        "revision_instruction": revision,
        "project_id": project_id,
        "run_id": run_id,
        "action": action,
        "instructions": INSTRUCTIONS,
        "approved_user_discovery": user,
        "prd_checkpoints": tech,
        "prd_sections": [{k: v for k, v in s.items() if k != "key"} for s in sections],
        "existing_sections": existing,
        "clarifications": clarifications or [],
        "regeneration_feedback": "",
        "target_section_id": target_section_id,
    }
    if settings and any(settings.values()):
        payload["document_settings"] = settings
    if new_answer_codes:
        payload["new_or_updated_answers"] = new_answer_codes
    return payload


def _clean_list(value: Any) -> list[str]:
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, list):
        return []
    return [str(x).strip() for x in value if isinstance(x, (str, int, float)) and str(x).strip()]


def _section_number(item: dict, by_code: dict[str, int]) -> int | None:
    raw = item.get("section_id", item.get("id"))
    if raw is None:
        raw = item.get("code") or item.get("section_code")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return by_code.get(str(raw).strip().upper())


def _is_section_item(value: dict) -> bool:
    return ("section_id" in value or "id" in value or "code" in value) and any(
        k in value for k in ("proposed_answer", "current_answer", "missing_information", "clarification_questions")
    )


def find_sections(raw: Any) -> list[dict]:
    """Every section item in the reply, however Agent5i wrapped it (JSON in strings, outputs lists...)."""
    for obj in find_json_objects(raw, lambda d: isinstance(d.get("sections"), list)):
        items = [x for x in obj["sections"] if isinstance(x, dict) and _is_section_item(x)]
        if items:
            return items
    return find_json_objects(raw, _is_section_item)


def normalize_reply(raw: Any, numbers: dict[int, str]) -> dict[str, dict]:
    """
    numbers: section_id (sort order) -> section_key of the sections asked for.
    Returns {section_key: {status, content, message, questions}} for the asked sections in the reply.
    complete: there is text (questions may come with it when information is still missing);
    insufficient: no text, only what is missing and the questions.
    """
    by_code = {f"PRDS{n:02d}": n for n in numbers}
    out: dict[str, dict] = {}
    for item in find_sections(raw):
        number = _section_number(item, by_code)
        key = numbers.get(number) if number is not None else None
        if key is None or key in out:
            continue  # not asked for, or a duplicate: the first one wins
        content = item.get("proposed_answer") or item.get("current_answer") or ""
        content = content.strip() if isinstance(content, str) else json.dumps(content, ensure_ascii=False)
        missing = _clean_list(item.get("missing_information"))
        out[key] = {
            "status": "complete" if content else "insufficient",
            "content": content,
            "message": "; ".join(missing)[:1000],
            "questions": _clean_list(item.get("clarification_questions"))[:MAX_QUESTIONS],
        }
    if not out:
        raise PrdReplyError("The PRD agent's reply has no sections array.")
    return out
