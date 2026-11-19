"""
The User Discovery agent: how it is called, what its answer must look like, and how each
written opinion is checked before it is stored.

Analogy: a specialist consultant. The case file goes in, and the opinion must come back in
the agreed form. Each opinion is checked on its own. A bad opinion is set aside and the others
are kept. Evidence the consultant cites from outside the case file is dropped.

The answer arrives wrapped. The platform's `message` is a JSON string whose `chunk_results`
key holds another JSON string, which holds `proposals`. We unwrap it layer by layer and read
nothing else.
"""

import json
import urllib.request
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError

from app.core.config import get_settings

PENDING_APPROVAL = "Pending Approval"
NEEDS_CLARIFICATION = "Needs Clarification"
AGENT_STATUSES = (PENDING_APPROVAL, NEEDS_CLARIFICATION)
REQUEST_PREFIX = "USER DISCOVERY REQUEST\n"
MAX_UNWRAP_DEPTH = 4


class AgentCallError(Exception):
    """The agent could not be reached, refused the request, or reported failure."""


class ContractError(Exception):
    """The agent answered, but the answer does not follow the agreed contract."""


@dataclass
class SentCheckpoint:
    """One checkpoint as it was sent: the chunks the agent may cite, and their mapping ids."""

    id: int
    code: str
    chunk_ids: frozenset[int]
    mapping_by_chunk: dict[int, int]


@dataclass
class ParsedEvidence:
    chunk_id: int
    reason: str


@dataclass
class ParsedProposal:
    checkpoint_id: int
    checkpoint_code: str
    proposed_answer: str
    agent_status: str
    is_completed: bool
    completion_score: float
    missing_information: list[str]
    clarification_questions: list[str]
    evidence: list[ParsedEvidence] = field(default_factory=list)


@dataclass
class ParseResult:
    accepted: dict[int, ParsedProposal] = field(default_factory=dict)
    failures: dict[int, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def call_user_agent(batch: dict) -> dict:
    """Sends one request and returns the platform's decoded response, unchanged."""
    settings = get_settings()
    if not (settings.agent5i_webhook_url and settings.agent5i_username and settings.agent5i_password):
        raise AgentCallError("Agent5i is not configured. Set the AGENT5I_* values in backend/.env.")

    body = {
        "username": settings.agent5i_username,
        "password": settings.agent5i_password,
        "name": settings.agent5i_user_agent_name,
        settings.agent5i_source_input_name: REQUEST_PREFIX + json.dumps(batch, ensure_ascii=False),
    }
    request = urllib.request.Request(
        settings.agent5i_webhook_url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.user_agent_timeout_seconds) as reply:
            raw = reply.read().decode("utf-8")
    except HTTPError as exc:
        raise AgentCallError(f"Agent5i returned HTTP {exc.code}.") from exc
    except (URLError, OSError) as exc:
        raise AgentCallError(f"Agent5i could not be reached: {exc}") from exc

    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ContractError("Agent5i response is not JSON.") from exc
    if not isinstance(data, dict) or data.get("success") is not True:
        raise AgentCallError("Agent5i reported an unsuccessful run.")
    return data


def final_output(data: dict) -> dict:
    """Returns the object holding `proposals`, unwrapping the platform's string layers."""
    if "message" not in data:
        raise ContractError("Agent response has no message.")
    return _unwrap(data["message"], 0)


def _unwrap(value, depth: int) -> dict:
    if depth > MAX_UNWRAP_DEPTH:
        raise ContractError("Agent output is nested too deeply.")
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except json.JSONDecodeError as exc:
            raise ContractError("Agent final output is not JSON.") from exc
        return _unwrap(decoded, depth + 1)
    if isinstance(value, dict):
        if isinstance(value.get("proposals"), list):
            return value
        if "chunk_results" in value:
            return _unwrap(value["chunk_results"], depth + 1)
    raise ContractError("Agent final output has no proposals list.")


def parse_proposals(output: dict, sent: list[SentCheckpoint]) -> ParseResult:
    """Checks every proposal against the checkpoints that were sent. Only those are considered."""
    by_code = {item.code: item for item in sent}
    result = ParseResult()

    for raw in output.get("proposals", []):
        if not isinstance(raw, dict):
            continue
        checkpoint = by_code.get(raw.get("checkpoint_code"))
        if checkpoint is None:
            continue  # the agent answered for a checkpoint we did not send
        if checkpoint.id in result.accepted:
            result.warnings.append(f"{checkpoint.code}: a second proposal was ignored.")
            continue
        try:
            result.accepted[checkpoint.id] = _validate(raw, checkpoint, result.warnings)
            result.failures.pop(checkpoint.id, None)
        except ContractError as exc:
            result.failures[checkpoint.id] = str(exc)

    for checkpoint in sent:
        if checkpoint.id not in result.accepted and checkpoint.id not in result.failures:
            result.failures[checkpoint.id] = "The agent returned no proposal for this checkpoint."
    return result


def _validate(raw: dict, checkpoint: SentCheckpoint, warnings: list[str]) -> ParsedProposal:
    if "checkpoint_id" in raw and (
        isinstance(raw["checkpoint_id"], bool) or raw["checkpoint_id"] != checkpoint.id
    ):
        raise ContractError("checkpoint_id does not match checkpoint_code.")

    status = raw.get("status")
    if status not in AGENT_STATUSES:
        raise ContractError(f"Unsupported status {status!r}.")

    text = raw.get("proposed_answer")
    if not isinstance(text, str):
        raise ContractError("proposed_answer must be text.")
    if status == PENDING_APPROVAL and not text.strip():
        raise ContractError("A Pending Approval proposal needs an answer.")

    completed = raw.get("is_completed")
    if not isinstance(completed, bool) or completed != (status == PENDING_APPROVAL):
        raise ContractError("is_completed does not match status.")

    score = raw.get("completion_score")
    if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= score <= 1:
        raise ContractError("completion_score must be a number from 0 to 1.")

    evidence: list[ParsedEvidence] = []
    for entry in _as_list(raw.get("evidence")):
        if not isinstance(entry, dict):
            continue
        chunk_id = _chunk_id(entry.get("chunk_id"))
        if chunk_id is None or chunk_id not in checkpoint.chunk_ids:
            warnings.append(
                f"{checkpoint.code}: cited chunk {entry.get('chunk_id')!r} was not sent for this checkpoint; ignored."
            )
            continue
        evidence.append(ParsedEvidence(chunk_id=chunk_id, reason=str(entry.get("reason") or "").strip()))

    return ParsedProposal(
        checkpoint_id=checkpoint.id,
        checkpoint_code=checkpoint.code,
        proposed_answer=text,
        agent_status=status,
        is_completed=completed,
        completion_score=round(float(score), 2),
        missing_information=_strings(raw.get("missing_information")),
        clarification_questions=_strings(raw.get("clarification_questions")),
        evidence=evidence,
    )


def _as_list(value) -> list:
    return value if isinstance(value, list) else []


def _strings(value) -> list[str]:
    return [item.strip() for item in _as_list(value) if isinstance(item, str) and item.strip()]


def _chunk_id(raw) -> int | None:
    """The agent sends chunk ids as text ("103"). Accepts text or a whole number, rejects anything else."""
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.strip().isdigit():
        return int(raw.strip())
    return None