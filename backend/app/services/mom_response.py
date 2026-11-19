"""
Finds the final answer inside an Agent5i run log.

Analogy: the reading desk for a long meeting log. The agent returns every message it wrote,
including the prompt and transcript. Only the final answer (meeting_output) is kept. It may
arrive as a dict, as JSON text, as a Python-style string, or inside the last message.
"""

import ast
import json
import re
from typing import Any

ANSWER_MARKERS = ('"meeting_output"', '"detailed_summary"', '"mom"')
MAX_DEPTH = 8
MAX_UNWRAP_DEPTH = 4


class MomResponseError(Exception):
    """The agent answered, but no usable meeting output was found."""


def extract_meeting_output(response: dict) -> Any:
    output = _find_answer(response, 0)
    if isinstance(output, str):
        parsed = _parse_answer_string(output)
        if parsed is not None:
            output = parsed
    if output is None:
        snippet = json.dumps(response, ensure_ascii=False)[:300]
        raise MomResponseError(f"The agent reply has no meeting output. It started with: {snippet}")
    return output


def unwrap_output(output: Any) -> tuple[Any, str | None]:
    """Return (body, project_title) from the agent's answer."""
    project_title = None
    for _ in range(MAX_UNWRAP_DEPTH):
        if isinstance(output, str):
            try:
                output = json.loads(output)
            except ValueError:
                break
        if not isinstance(output, dict):
            break

        project_title = output.get("project_title") or project_title
        if "meeting_output" in output:
            output = output["meeting_output"]
            continue
        for key in ("detailed_summary", "mom", "minutes_of_meeting"):
            if key in output:
                output = output[key]
                break
        else:
            for key in ("document", "description", "content", "text", "markdown", "body"):
                value = output.get(key)
                if isinstance(value, (str, dict, list)) and value:
                    output = value
                    break
            else:
                break
    return output, project_title


def _norm_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _balanced_prefix(text: str) -> str:
    """The first complete {...} or [...] at the start of text."""
    if not text or text[0] not in "{[":
        return text
    depth = 0
    quote = None
    escaped = False
    for index, char in enumerate(text):
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = None
            continue
        if char in ("'", '"'):
            quote = char
        elif char in "{[":
            depth += 1
        elif char in "}]":
            depth -= 1
            if depth == 0:
                return text[: index + 1]
    return text


def _parse_answer_string(text: str, depth: int = 0) -> Any:
    """Read the answer from one string. None when it holds no answer."""
    if depth > MAX_DEPTH:
        return None
    stripped = text.strip()

    # Python-style:  meeting_output={'type': ..., 'description': "..."}
    marker = "meeting_output="
    position = stripped.find(marker)
    if position != -1:
        rest = stripped[position + len(marker):].strip()
        for candidate in (rest, _balanced_prefix(rest)):
            try:
                return ast.literal_eval(candidate)
            except (ValueError, SyntaxError):
                pass
            try:
                return json.loads(candidate)
            except ValueError:
                pass

    # A message written as   content='...' additional_kwargs={...}
    message = re.match(r"""content=('(?:[^'\\]|\\.)*'|"(?:[^"\\]|\\.)*")""", stripped, re.S)
    if message:
        try:
            inner = ast.literal_eval(message.group(1))
        except (ValueError, SyntaxError):
            return None
        if isinstance(inner, str) and any(marker in inner for marker in ANSWER_MARKERS):
            return _parse_answer_string(inner, depth + 1)
        return None

    # Plain JSON text that contains the answer.
    if any(marker in stripped for marker in ANSWER_MARKERS):
        start = stripped.find("{")
        if start != -1:
            try:
                parsed, _ = json.JSONDecoder().raw_decode(stripped[start:])
            except ValueError:
                return None
            return _find_answer(parsed, depth + 1)
    return None


def _find_answer(obj: Any, depth: int) -> Any:
    if obj is None or depth > MAX_DEPTH:
        return None
    if isinstance(obj, str):
        return _parse_answer_string(obj, depth + 1)
    if isinstance(obj, dict):
        if "meeting_output" in obj:
            return obj["meeting_output"]
        if "mom" in obj or "detailed_summary" in obj:
            return obj

        first, middle, last = [], [], []
        for key in obj:
            name = _norm_key(key)
            if "final" in name or name in ("output", "result", "response", "content", "data"):
                first.append(key)
            elif name in ("messages", "message"):
                last.append(key)
            elif name in ("inputvariables", "sourcefiles", "input"):
                continue
            else:
                middle.append(key)
        for key in first + middle + last:
            found = _find_answer(obj[key], depth + 1)
            if found is not None:
                return found
        return None
    if isinstance(obj, list):
        for item in reversed(obj):
            found = _find_answer(item, depth + 1)
            if found is not None:
                return found
    return None
