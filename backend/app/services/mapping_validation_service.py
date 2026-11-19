"""
Checks what the Helper Agent returned before anything is saved.

Analogy: the quality inspector at the end of the production line. The agent is fast but
imperfect. The inspector checks every item: is the quote really on the page, is the
checkpoint on the approved list, is there a reason, did every page get an answer, and do
the saved character positions point at the same words? Bad items are removed and
reported; the rest of the box still ships.

Correctness: the agent is never trusted for positions. This module finds each quote in
the real chunk text and calculates the absolute offset itself, then checks it against the
stored content before a match is accepted.

Security: the agent's output is untrusted input. Every field is type-checked before use,
and nothing from it is ever used as a database key except a checkpoint ID that is present
in the active checkpoint list sent with the request.
"""

import logging
import re
from dataclasses import dataclass, field
from typing import Any

from app.services.agent_reply import find_json_object

log = logging.getLogger(__name__)

MAX_QUOTE_WORDS = 80


class MappingResponseError(Exception):
    """The agent's reply has no usable chunk_results list. The whole batch is treated as failed."""


@dataclass(frozen=True)
class ValidMatch:
    chunk_id: int
    checkpoint_id: int
    evidence_quote: str
    reason: str
    evidence_start_char: int
    evidence_end_char: int


@dataclass
class BatchValidation:
    matches: list[ValidMatch] = field(default_factory=list)
    matched_chunk_ids: set[int] = field(default_factory=set)
    warnings: list[str] = field(default_factory=list)
    dropped: int = 0


def find_checkpoint_output(raw: Any) -> dict | None:
    """The object that holds chunk_results, wherever the agent wrapped it."""
    return find_json_object(raw, lambda obj: isinstance(obj.get("chunk_results"), list))


def locate_quote(chunk_text: str, quote: Any) -> tuple[int, int] | None:
    """
    Find the quote inside the chunk and return its (start, end) in chunk_text.

    Exact text is tried first. Then whitespace and letter case are relaxed, so a quote
    that differs only in spacing or capitals still matches. The returned span is always
    taken from the original chunk text, never from the agent's copy of it.
    """
    if not isinstance(quote, str):
        return None
    stripped = quote.strip()
    if not stripped:
        return None

    index = chunk_text.find(stripped)
    if index != -1:
        return index, index + len(stripped)

    parts = stripped.split()
    if len(parts) > MAX_QUOTE_WORDS:
        return None
    pattern = r"\s+".join(re.escape(part) for part in parts)
    match = re.search(pattern, chunk_text, flags=re.IGNORECASE)
    if match is None:
        return None
    return match.start(), match.end()


def validate_batch(
    chunks: list[dict],
    checkpoints: dict[int, dict],
    output: dict,
    content_texts: dict[int, str],
) -> BatchValidation:
    """
    Apply the checks in order and return the matches that passed.

    chunks: the batch as sent to the agent, in order. Each needs id, chunk_text, start_char,
            and context_content_id.
    checkpoints: active checkpoints keyed by id, each with code and pillar_name.
    output: the object returned by find_checkpoint_output.
    content_texts: full extracted text keyed by context_content_id, used for the final
            offset check.

    A bad match is dropped with a warning; the other matches for the same chunk are kept.
    Only a reply with no usable chunk_results raises, and that fails the whole batch.
    """
    entries = output.get("chunk_results")
    if not isinstance(entries, list):
        raise MappingResponseError("The agent reply has no chunk_results list.")

    result = BatchValidation()
    chunk_by_id = {chunk["id"]: chunk for chunk in chunks}
    returned = _index_entries(entries, chunk_by_id, result)

    # Coverage: every chunk in the batch needs an entry, even if the agent left it out.
    for chunk in chunks:
        if chunk["id"] not in returned:
            _warn(result, f"Chunk {chunk['id']}: the agent returned no entry, so it is treated as unmatched.")
            returned[chunk["id"]] = {"chunk_id": chunk["id"], "matches": []}

    for chunk in chunks:
        matches = returned[chunk["id"]].get("matches")
        if not isinstance(matches, list):
            _warn(result, f"Chunk {chunk['id']}: matches is not a list, so it is treated as unmatched.")
            continue
        _validate_chunk_matches(chunk, matches, checkpoints, content_texts, result)

    return result


def _index_entries(entries: list, chunk_by_id: dict[int, dict], result: BatchValidation) -> dict[int, dict]:
    """Keep one entry per chunk that was actually sent. Anything else is dropped."""
    returned: dict[int, dict] = {}
    for entry in entries:
        if not isinstance(entry, dict):
            _warn(result, "A chunk entry is not an object and was dropped.")
            continue
        chunk_id = entry.get("chunk_id")
        if chunk_id not in chunk_by_id:
            _warn(result, f"Chunk {chunk_id}: dropped, because it was not in this batch.")
            continue
        if chunk_id in returned:
            _warn(result, f"Chunk {chunk_id}: a second entry was returned and ignored.")
            continue
        returned[chunk_id] = entry
    return returned


def _validate_chunk_matches(
    chunk: dict,
    matches: list,
    checkpoints: dict[int, dict],
    content_texts: dict[int, str],
    result: BatchValidation,
) -> None:
    chunk_id = chunk["id"]
    seen_checkpoints: set[int] = set()

    for raw_match in matches:
        if not isinstance(raw_match, dict):
            _drop(result, f"Chunk {chunk_id}: a match is not an object and was dropped.")
            continue

        # 1. Evidence: the quote must be in this chunk's text.
        span = locate_quote(chunk["chunk_text"], raw_match.get("evidence_quote"))
        if span is None:
            _drop(
                result,
                f"Chunk {chunk_id}: dropped the {raw_match.get('checkpoint_code', 'unknown')} match, "
                "because its evidence quote is not in this chunk.",
            )
            continue

        # 2. Checkpoint: the ID must be an active checkpoint, and each may appear once per chunk.
        checkpoint_id = raw_match.get("checkpoint_id")
        checkpoint = checkpoints.get(checkpoint_id) if isinstance(checkpoint_id, int) else None
        if checkpoint is None:
            _drop(result, f"Chunk {chunk_id}: dropped a match with unknown checkpoint_id {checkpoint_id!r}.")
            continue
        if checkpoint_id in seen_checkpoints:
            _drop(result, f"Chunk {chunk_id}: dropped a repeated match for checkpoint {checkpoint['code']}.")
            continue
        if raw_match.get("checkpoint_code") != checkpoint["code"]:
            _warn(
                result,
                f"Chunk {chunk_id}: corrected checkpoint_code {raw_match.get('checkpoint_code')!r} "
                f"to {checkpoint['code']!r} for checkpoint_id {checkpoint_id}.",
            )
        if raw_match.get("pillar_name") != checkpoint["pillar_name"]:
            _warn(
                result,
                f"Chunk {chunk_id}: corrected pillar_name {raw_match.get('pillar_name')!r} "
                f"to {checkpoint['pillar_name']!r} for checkpoint_id {checkpoint_id}.",
            )

        # 3. Reason: a match without an explanation is not reviewable, so it is dropped.
        reason = raw_match.get("reason")
        if not isinstance(reason, str) or not reason.strip():
            _drop(result, f"Chunk {chunk_id}: dropped the {checkpoint['code']} match, because it has no reason.")
            continue

        # 5. Offsets: convert to content positions and check against the stored text.
        local_start, local_end = span
        absolute_start = chunk["start_char"] + local_start
        absolute_end = chunk["start_char"] + local_end
        quote = chunk["chunk_text"][local_start:local_end]
        content_text = content_texts.get(chunk["context_content_id"])
        if content_text is None or content_text[absolute_start:absolute_end] != quote:
            _drop(
                result,
                f"Chunk {chunk_id}: dropped the {checkpoint['code']} match, because its position "
                "does not match the stored text.",
            )
            continue

        seen_checkpoints.add(checkpoint_id)
        result.matches.append(
            ValidMatch(
                chunk_id=chunk_id,
                checkpoint_id=checkpoint_id,
                evidence_quote=quote,
                reason=reason.strip(),
                evidence_start_char=absolute_start,
                evidence_end_char=absolute_end,
            )
        )
        result.matched_chunk_ids.add(chunk_id)


def _drop(result: BatchValidation, message: str) -> None:
    result.dropped += 1
    _warn(result, message)


def _warn(result: BatchValidation, message: str) -> None:
    result.warnings.append(message)
    log.warning("Mapping validation: %s", message)
