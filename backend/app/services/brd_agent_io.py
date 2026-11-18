"""
What we send to the BRD agent and how we read its reply. Pure functions: no database, no network.

Analogy: the envelope and the letter opener. build_agent_input() writes the letter (the control
block plus the approved discovery answers), and normalize_agent_response() opens the reply and
lays the 14 sections out the same way every time, however the agent wrapped them.

The request format is the one the BRD Extraction Agent already understands (AGENT_REQUEST ...
END_AGENT_REQUEST, then ORIGINAL_SOURCE_DOCUMENT). The only change from the stand-alone BRD app
is what follows ORIGINAL_SOURCE_DOCUMENT: the project's APPROVED checkpoint answers instead of
the text of uploaded files.
"""

import json
import re
from typing import Any

from app.services.agent_reply import find_json_object

MODE_GENERATE_ALL = "generate_all"
MODE_REGENERATE_SECTION = "regenerate_section"
MODE_CLARIFY_QUESTIONS = "clarify_questions"

SECTION_STATUSES = {"complete", "insufficient", "skipped"}
MAX_QUESTIONS = 3
NO_CONTENT_MSG = "No approved discovery answer covers this section yet. Use Clarify to add details."

# Sent before the clarification on the 2nd and 3rd regenerate attempt, when the user already gave
# facts for the section and the agent still answered "insufficient".
REGENERATE_PREFIXES = (
    "",
    "IMPORTANT: The facts below were confirmed by the user. The target section MUST be returned as "
    "complete with a freshly rewritten version. Do not return insufficient or 'No content found'. "
    "Return ONLY the required JSON object, with no text before or after it.\n\n",
    "FINAL ATTEMPT. Mode is regenerate_section. The user-confirmed facts below are valid evidence. "
    "Return the target section with status complete and a rewritten, re-organized version of these facts. "
    "Return the other 13 sections as skipped. A status of insufficient is NOT allowed. "
    "Return ONLY the required JSON object, with no text before or after it.\n\n",
)
USER_CONTENT_PREFIX = (
    "USER-CONFIRMED SECTION CONTENT (treat as user-provided project facts; rewrite it into a fresh, "
    "better-structured version and merge with relevant source facts):\n"
)


class AgentReplyError(ValueError):
    """The reply did not contain the structured BRD object."""


def build_source_text(answers: list[dict]) -> str:
    """
    The approved answers, one block per checkpoint, in the order given.
    Each answer: {"code", "name", "pillar", "question", "answer"}.
    """
    if not answers:
        return "APPROVED DISCOVERY ANSWERS\n\nNo approved answers are available for this section yet."
    blocks = [
        f"--- CHECKPOINT {a['code']}: {a['name']} ({a['pillar']} pillar) ---\n"
        f"Question: {a['question']}\n"
        f"Approved answer:\n{(a['answer'] or '').strip()}"
        for a in answers
    ]
    return "APPROVED DISCOVERY ANSWERS\n\n" + "\n\n".join(blocks)


def build_document_settings(title: str | None, audience: str | None, scope: str | None) -> str:
    """The "Configure the draft" choices, placed before the answers. Empty when none is set."""
    lines = []
    if title:
        lines.append(f"Document title: {title}")
    if audience:
        lines.append(f"Audience: {audience} (write for this reader)")
    if scope:
        lines.append(f"Scope: {scope} (cover only this scope)")
    return ("DOCUMENT SETTINGS\n" + "\n".join(lines) + "\n\n") if lines else ""


def build_agent_input(
    source_text: str,
    mode: str,
    target_section: str = "",
    clarification: str = "",
    current_section_content: str = "",
) -> str:
    """The single text input of the BRD agent: control block, then the approved answers."""
    control = (
        "AGENT_REQUEST\n"
        f"mode: {mode}\n"
        f"target_section: {target_section}\n"
        f"clarification:\n{clarification}\n"
        f"current_section_content:\n{current_section_content}\n"
        "END_AGENT_REQUEST\n\n"
        "ORIGINAL_SOURCE_DOCUMENT:\n"
    )
    return control + source_text


def format_clarifications(pairs: list[tuple[str, str]]) -> str:
    """[(question, answer)] -> "Q1: ...\\nA1: ..." blocks, the format the agent already reads."""
    return "\n\n".join(
        f"Q{i}: {question}\nA{i}: {answer.strip()}" for i, (question, answer) in enumerate(pairs, start=1)
    )


def clean_text(value: Any) -> str:
    """Turn escaped sequences into real line breaks so Markdown renders properly."""
    if value is None:
        return ""
    if isinstance(value, (list, dict)):
        value = json.dumps(value, ensure_ascii=False, indent=2)
    text = str(value).replace("\r\n", "\n").strip()
    text = re.sub(r"^```(?:markdown|md|json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    # The agent sometimes double-escapes: a literal backslash + n instead of a newline.
    if text.count("\\n") > text.count("\n"):
        text = text.replace("\\r\\n", "\n").replace("\\n", "\n").replace("\\t", " ")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_questions(raw: Any) -> list[str]:
    if not isinstance(raw, list):
        return []
    return [q for q in (clean_text(item) for item in raw) if q][:MAX_QUESTIONS]


def _is_brd_object(value: dict) -> bool:
    sections = value.get("sections")
    if isinstance(sections, dict) and ("mode" in value or sections or "questions" in value):
        return True
    return isinstance(value.get("questions"), list) and bool(value["questions"])


def normalize_agent_response(raw: Any, section_keys: list[str], mode: str, target_section: str = "") -> dict:
    """
    Every section key gets {"status", "content", "message", "questions"}:
    - complete     -> content is set, message is empty
    - insufficient -> content is empty, message says why (NO_CONTENT_MSG when the agent gave none)
    - skipped      -> the agent left the section alone (single-section modes only)
    Raises AgentReplyError when the structured object is not in the reply.
    """
    found = find_json_object(raw, _is_brd_object)
    if found is None:
        raise AgentReplyError("The BRD agent's reply did not contain the structured BRD object.")

    raw_sections = found.get("sections") if isinstance(found.get("sections"), dict) else {}
    sections: dict[str, dict] = {}
    for key in section_keys:
        item = raw_sections.get(key, {})
        if not isinstance(item, dict):
            content = clean_text(item)
            item = {"status": "complete" if content else "insufficient", "content": content}
        status = item.get("status", "insufficient")
        if status not in SECTION_STATUSES:
            status = "insufficient"
        content = clean_text(item.get("content", ""))
        message = clean_text(item.get("message", ""))

        if status == "complete" and not content:
            status = "insufficient"
        if status == "skipped" and mode == MODE_GENERATE_ALL:
            status = "insufficient"
        if status == "insufficient":
            content = ""
            message = message or NO_CONTENT_MSG
        elif status == "complete":
            message = ""
        questions = _clean_questions(
            item.get("questions") or item.get("clarification_questions") or item.get("clarify_questions") or []
        )
        sections[key] = {"status": status, "content": content, "message": message, "questions": questions}

    return {
        "mode": found.get("mode") or mode,
        "target_section": found.get("target_section") or target_section or "",
        "sections": sections,
        "questions": _clean_questions(found.get("questions", [])),
    }
