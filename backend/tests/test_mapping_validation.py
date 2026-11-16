# tests/test_mapping_validation.py
"""
Tests for reading and checking the Helper Agent's reply. No database and no network:
the agent is represented by a fixture copied from the Batch 2 run.
Run from backend/: python -m pytest -q tests/test_mapping_validation.py
"""

import copy
import json
import socket
from urllib.error import HTTPError, URLError

import pytest

from app.services import agent_client
from app.services.agent_client import (
    AgentConfigurationError,
    AgentConnectionError,
    AgentHttpError,
    AgentTimeoutError,
    call_helper_agent,
)
from app.services.mapping_validation_service import (
    MappingResponseError,
    find_checkpoint_output,
    locate_quote,
    validate_batch,
)

CHUNK_TEXTS = {
    131: "The ERP runs on a fixed on-premise server and cannot be upgraded before 2027. Orders are keyed in by hand.",
    132: "Staff log in to the intranet with a single shared account per warehouse.",
    133: "The ERP and intranet are hosted in a single data centre with one production and one test environment.",
    134: "Warehouse supervisors check order status several times per shift and frequently call the dispatch desk when the dashboard is out of date.",
    135: "Shipping labels are generated from order records that the shipping tool imports from the nightly export",
    136: "Monthly stock counts are reconciled by hand.",
}

CHECKPOINTS = {
    301: {"id": 301, "code": "TECH01", "pillar_name": "Tech Discovery"},
    302: {"id": 302, "code": "TECH02", "pillar_name": "Tech Discovery"},
    303: {"id": 303, "code": "TECH03", "pillar_name": "Tech Discovery"},
    304: {"id": 304, "code": "TECH04", "pillar_name": "Tech Discovery"},
    305: {"id": 305, "code": "TECH05", "pillar_name": "Tech Discovery"},
    204: {"id": 204, "code": "DATA04", "pillar_name": "Data Discovery"},
}

# The agent's chunk_results from the Batch 2 run, exactly as it was returned.
BATCH2_OUTPUT = {
    "project_id": 1,
    "chunk_results": [
        {
            "chunk_id": 131,
            "matches": [
                {
                    "checkpoint_id": 301,
                    "checkpoint_code": "TECH01",
                    "pillar_name": "Tech Discovery",
                    "evidence_quote": "The ERP runs on a fixed on-premise server",
                    "reason": "The evidence identifies the ERP as an existing platform.",
                },
                {
                    "checkpoint_id": 303,
                    "checkpoint_code": "TECH03",
                    "pillar_name": "Tech Discovery",
                    "evidence_quote": "The ERP runs on a fixed on-premise server and cannot be upgraded before 2027.",
                    "reason": "The evidence documents an explicit infrastructure restriction.",
                },
            ],
        },
        {
            "chunk_id": 132,
            "matches": [
                {
                    "checkpoint_id": 304,
                    "checkpoint_code": "TECH04",
                    "pillar_name": "Tech Discovery",
                    "evidence_quote": "Staff log in to the intranet with a single shared account per warehouse.",
                    "reason": "The evidence documents shared warehouse credentials.",
                }
            ],
        },
        {
            "chunk_id": 133,
            "matches": [
                {
                    "checkpoint_id": 305,
                    "checkpoint_code": "TECH05",
                    "pillar_name": "Tech Discovery",
                    "evidence_quote": "The ERP and intranet are hosted in a single data centre with one production and one test environment.",
                    "reason": "The evidence documents the hosting location and environments.",
                }
            ],
        },
        {
            "chunk_id": 134,
            "matches": [
                {
                    "checkpoint_id": 301,
                    "checkpoint_code": "TECH01",
                    "pillar_name": "Tech Discovery",
                    "evidence_quote": "Warehouse supervisors check order status several times per shift and frequently call the dispatch desk when the dashboard is out of date.",
                    "reason": "The evidence identifies the dashboard as an existing system.",
                }
            ],
        },
        {
            "chunk_id": 135,
            "matches": [
                {
                    "checkpoint_id": 204,
                    "checkpoint_code": "DATA04",
                    "pillar_name": "Data Discovery",
                    "evidence_quote": "Shipping labels are generated from order records that the shipping tool imports from the nightly export",
                    "reason": "The evidence documents order records moving from a nightly export into the shipping tool.",
                },
                {
                    "checkpoint_id": 302,
                    "checkpoint_code": "TECH02",
                    "pillar_name": "Tech Discovery",
                    "evidence_quote": "the shipping tool imports from the nightly export",
                    "reason": "The evidence identifies an interaction between the shipping tool and the export.",
                },
            ],
        },
        {"chunk_id": 136, "matches": []},
    ],
}


def _batch():
    """Chunks laid out in one content text, the way chunking stores them (start_char is the real offset)."""
    chunks, content = [], ""
    for chunk_id, text in CHUNK_TEXTS.items():
        chunks.append({"id": chunk_id, "context_content_id": 42, "chunk_number": len(chunks) + 1,
                       "chunk_text": text, "page_number": None, "start_char": len(content)})
        content += text + "\n\n"
    return chunks, {42: content}


def _validate(output, chunks=None, content_texts=None):
    if chunks is None:
        chunks, content_texts = _batch()
    return validate_batch(chunks, CHECKPOINTS, output, content_texts)


def _output(*entries):
    return {"project_id": 1, "chunk_results": list(entries)}


def _entry(chunk_id, *matches):
    return {"chunk_id": chunk_id, "matches": list(matches)}


def _match(checkpoint_id, quote, reason="A valid reason."):
    cp = CHECKPOINTS[checkpoint_id]
    return {"checkpoint_id": checkpoint_id, "checkpoint_code": cp["code"], "pillar_name": cp["pillar_name"],
            "evidence_quote": quote, "reason": reason}


# --- finding the answer inside the reply -----------------------------------------------


def test_nested_string_wrappers_are_unwrapped_to_the_chunk_results():
    inner = json.dumps({"checkpoint_mapping_output": BATCH2_OUTPUT})
    raw = {"success": True, "message": {"final_response": "```json\n" + inner + "\n```"},
           "metainfo": {"model": ["gpt-5.6-luna"]}}

    found = find_checkpoint_output(raw)

    assert found is not None
    assert [entry["chunk_id"] for entry in found["chunk_results"]] == [131, 132, 133, 134, 135, 136]


def test_the_batch2_sample_keeps_every_valid_match():
    chunks, content_texts = _batch()

    result = _validate(BATCH2_OUTPUT, chunks, content_texts)

    assert len(result.matches) == 7
    assert result.dropped == 0
    assert result.warnings == []
    assert result.matched_chunk_ids == {131, 132, 133, 134, 135}


def test_every_saved_match_points_at_its_exact_quote_in_the_content():
    chunks, content_texts = _batch()

    result = _validate(BATCH2_OUTPUT, chunks, content_texts)

    for match in result.matches:
        content = content_texts[42]
        assert content[match.evidence_start_char : match.evidence_end_char] == match.evidence_quote


# --- the validation rules ------------------------------------------------------------


def test_a_quote_that_is_not_in_the_chunk_is_dropped_and_the_rest_are_kept(caplog):
    output = copy.deepcopy(BATCH2_OUTPUT)
    output["chunk_results"][0]["matches"][0]["evidence_quote"] = "The ERP is on a cloud platform"

    result = _validate(output)

    kept_for_131 = [m.checkpoint_id for m in result.matches if m.chunk_id == 131]
    assert kept_for_131 == [303]
    assert result.dropped == 1
    assert any("evidence quote is not in this chunk" in w for w in result.warnings)
    assert "evidence quote is not in this chunk" in caplog.text


def test_an_unknown_checkpoint_id_is_dropped():
    unknown = {"checkpoint_id": 999, "checkpoint_code": "XXX", "pillar_name": "Tech Discovery",
               "evidence_quote": "The ERP runs on a fixed on-premise server", "reason": "Not an active checkpoint."}
    output = _output(_entry(131, unknown))

    result = _validate(output)

    assert result.matches == []
    assert any("unknown checkpoint_id 999" in w for w in result.warnings)


def test_a_repeated_checkpoint_in_one_chunk_keeps_only_the_first():
    first = _match(301, "The ERP runs on a fixed on-premise server", "First reason.")
    second = _match(301, "The ERP runs on a fixed on-premise server", "Second reason.")

    result = _validate(_output(_entry(131, first, second)))

    assert len(result.matches) == 1
    assert result.matches[0].reason == "First reason."
    assert any("repeated match" in w for w in result.warnings)


def test_a_mismatched_checkpoint_code_is_corrected_from_the_database():
    wrong = _match(301, "The ERP runs on a fixed on-premise server")
    wrong["checkpoint_code"] = "TECH99"
    wrong["pillar_name"] = "Wrong Pillar"

    result = _validate(_output(_entry(131, wrong)))

    assert len(result.matches) == 1
    assert result.matches[0].checkpoint_id == 301
    assert any("corrected checkpoint_code 'TECH99' to 'TECH01'" in w for w in result.warnings)
    assert any("corrected pillar_name" in w for w in result.warnings)


def test_a_missing_chunk_entry_is_added_as_empty_with_a_warning():
    output = copy.deepcopy(BATCH2_OUTPUT)
    output["chunk_results"] = [e for e in output["chunk_results"] if e["chunk_id"] != 134]

    result = _validate(output)

    assert 134 not in result.matched_chunk_ids
    assert any("Chunk 134: the agent returned no entry" in w for w in result.warnings)
    assert {m.chunk_id for m in result.matches} == {131, 132, 133, 135}


def test_an_entry_for_a_chunk_that_was_not_sent_is_dropped():
    output = copy.deepcopy(BATCH2_OUTPUT)
    output["chunk_results"].append(_entry(999, _match(301, "The ERP runs on a fixed on-premise server")))

    result = _validate(output)

    assert all(m.chunk_id != 999 for m in result.matches)
    assert any("Chunk 999: dropped, because it was not in this batch." in w for w in result.warnings)


def test_a_match_with_an_empty_reason_is_dropped():
    output = _output(_entry(131, _match(301, "The ERP runs on a fixed on-premise server", "   ")))

    result = _validate(output)

    assert result.matches == []
    assert any("has no reason" in w for w in result.warnings)


def test_a_chunk_whose_matches_are_all_invalid_is_not_marked_as_matched():
    output = _output(_entry(134, _match(301, "a sentence that is not in the chunk")))

    result = _validate(output)

    assert result.matches == []
    assert 134 not in result.matched_chunk_ids


def test_quote_matching_ignores_case_and_spacing_but_stores_the_original_text():
    loose = "the  erp RUNS on a fixed on-premise server"

    result = _validate(_output(_entry(131, _match(301, loose))))

    assert len(result.matches) == 1
    assert result.matches[0].evidence_quote == "The ERP runs on a fixed on-premise server"


def test_locate_quote_returns_the_span_inside_the_chunk():
    text = "Intro text. The ERP runs on a fixed on-premise server. More text."

    assert locate_quote(text, "The ERP runs on a fixed on-premise server") == (12, 53)
    assert locate_quote(text, "   ") is None
    assert locate_quote(text, None) is None


def test_a_reply_without_chunk_results_fails_the_batch():
    with pytest.raises(MappingResponseError):
        _validate({"project_id": 1})


# --- calling the agent: which failures are retried ------------------------------------


@pytest.fixture
def configured(monkeypatch):
    class _Settings:
        agent5i_webhook_url = "https://agent.example.test/webhook/"
        agent5i_username = "user@example.test"
        agent5i_password = "not-a-real-password"
        agent5i_agent_name = "Discovery Hub Helper Agent"
        agent5i_source_input_name = "source_files"
        agent5i_timeout_seconds = 5

    monkeypatch.setattr(agent_client, "get_settings", lambda: _Settings())


def _fake_urlopen(monkeypatch, behaviour):
    def _open(request, timeout):
        if isinstance(behaviour, BaseException):
            raise behaviour
        return behaviour

    monkeypatch.setattr(agent_client, "urlopen", _open)


class _Response:
    def __init__(self, body: bytes) -> None:
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def test_a_successful_call_returns_the_decoded_reply(monkeypatch, configured):
    _fake_urlopen(monkeypatch, _Response(b'{"success": true}'))

    assert call_helper_agent({"project_id": 1}) == {"success": True}


def test_a_401_is_not_retried(monkeypatch, configured):
    _fake_urlopen(monkeypatch, HTTPError("https://x", 401, "Unauthorized", None, None))

    with pytest.raises(AgentHttpError) as info:
        call_helper_agent({"project_id": 1})

    assert info.value.status_code == 401
    assert info.value.retryable is False


def test_a_503_is_retryable(monkeypatch, configured):
    _fake_urlopen(monkeypatch, HTTPError("https://x", 503, "Unavailable", None, None))

    with pytest.raises(AgentHttpError) as info:
        call_helper_agent({"project_id": 1})

    assert info.value.retryable is True


def test_a_timeout_is_retryable(monkeypatch, configured):
    _fake_urlopen(monkeypatch, socket.timeout("timed out"))

    with pytest.raises(AgentTimeoutError) as info:
        call_helper_agent({"project_id": 1})

    assert info.value.retryable is True


def test_a_timeout_wrapped_in_a_url_error_is_still_a_timeout(monkeypatch, configured):
    _fake_urlopen(monkeypatch, URLError(socket.timeout("timed out")))

    with pytest.raises(AgentTimeoutError):
        call_helper_agent({"project_id": 1})


def test_a_connection_failure_is_not_retried(monkeypatch, configured):
    _fake_urlopen(monkeypatch, URLError(ConnectionRefusedError()))

    with pytest.raises(AgentConnectionError) as info:
        call_helper_agent({"project_id": 1})

    assert info.value.retryable is False


def test_missing_configuration_is_a_configuration_error_and_is_not_retried(monkeypatch):
    class _Empty:
        agent5i_webhook_url = ""
        agent5i_username = ""
        agent5i_password = ""

    monkeypatch.setattr(agent_client, "get_settings", lambda: _Empty())

    with pytest.raises(AgentConfigurationError) as info:
        call_helper_agent({"project_id": 1})

    assert info.value.retryable is False
