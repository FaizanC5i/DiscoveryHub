"""
Finds the useful object inside an agent reply, however many layers of wrapping it has.

Analogy: unwrapping a parcel inside several boxes. Each box may be a plain object, a string
holding JSON, or a markdown code fence. We open layers until we find the item we asked for,
and stop after a fixed number of layers so a malformed reply cannot loop forever.
"""

import json
import re
from collections.abc import Callable
from typing import Any

MAX_UNWRAP_DEPTH = 10
UNWRAP_KEYS = (
    "output",
    "result",
    "response",
    "final_response",
    "message",
    "checkpoint_mapping_output",
    "text",
    "content",
    "data",
)


def find_json_object(raw: Any, accepts: Callable[[dict], bool], depth: int = 0) -> dict | None:
    """Return the first dict, anywhere in the reply, for which accepts(dict) is True."""
    if depth > MAX_UNWRAP_DEPTH:
        return None

    if isinstance(raw, dict):
        if accepts(raw):
            return raw
        for key in UNWRAP_KEYS:
            if key in raw:
                found = find_json_object(raw[key], accepts, depth + 1)
                if found is not None:
                    return found
        for value in raw.values():
            found = find_json_object(value, accepts, depth + 1)
            if found is not None:
                return found
        return None

    if isinstance(raw, list):
        for value in raw:
            found = find_json_object(value, accepts, depth + 1)
            if found is not None:
                return found
        return None

    if isinstance(raw, str):
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        try:
            return find_json_object(json.loads(text), accepts, depth + 1)
        except ValueError:
            pass
        # The text may hold JSON after some prose. Try each opening brace in turn.
        decoder = json.JSONDecoder()
        index = text.find("{")
        while index != -1:
            try:
                obj, _ = decoder.raw_decode(text[index:])
                found = find_json_object(obj, accepts, depth + 1)
                if found is not None:
                    return found
            except ValueError:
                pass
            index = text.find("{", index + 1)
    return None
