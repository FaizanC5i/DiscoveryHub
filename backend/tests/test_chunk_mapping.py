# tests/test_chunk_mapping.py
"""
Checkpoint mapping against the real database. The Helper Agent is replaced by a fake that
answers from a fixed table, so no network call is made. Users are deleted at the end, which
cascades to their rows.
Run from backend/: python -m pytest -q tests/test_chunk_mapping.py
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import true

from app.core.time import utc_now
from app.db.models import (
    AgentRun,
    ContextChunk,
    ContextCheckpointMapping,
    ContextContent,
    ContextSource,
    MappingEvidence,
)
from app.db.session import get_session_factory
from app.main import app
from app.services import agent_client, chunk_mapping_service
from app.services.agent_client import AgentHttpError, AgentTimeoutError

CHUNK_TEXTS = [
    "The ERP runs on a fixed on-premise server and cannot be upgraded before 2027. Orders are keyed in by hand.",
    "Staff log in to the intranet with a single shared account per warehouse.",
    "Warehouse supervisors check order status several times per shift and frequently call the dispatch desk when the dashboard is out of date.",
    "Monthly stock counts are reconciled by hand.",
]

# Answers the fake agent gives for each chunk text: (quote, checkpoint_id, reason).
ANSWERS = {
    CHUNK_TEXTS[0]: [
        ("The ERP runs on a fixed on-premise server and cannot be upgraded before 2027.", 303,
         "An explicit infrastructure restriction with a time limit."),
    ],
    CHUNK_TEXTS[1]: [
        ("Staff log in to the intranet with a single shared account per warehouse.", 304,
         "Documents shared warehouse credentials."),
    ],
    CHUNK_TEXTS[2]: [
        ("the dashboard is out of date", 301, "The dashboard is an existing system used for order status."),
    ],
    CHUNK_TEXTS[3]: [],
}


@pytest.fixture
def fake_agent(monkeypatch):
    """Replaces the webhook. Records every call and can be told to fail."""
    state = {"calls": 0, "error": None, "bad_quote_for": None}

    def _call(payload):
        state["calls"] += 1
        if state["error"] is not None:
            raise state["error"]
        entries = []
        for chunk in payload["context_chunks"]:
            matches = []
            for quote, checkpoint_id, reason in ANSWERS.get(chunk["chunk_text"], []):
                if chunk["chunk_text"] == state["bad_quote_for"]:
                    quote = "a sentence that is not in this chunk"
                checkpoint = next(c for c in payload["discovery_checkpoints"] if c["id"] == checkpoint_id)
                matches.append({
                    "checkpoint_id": checkpoint_id,
                    "checkpoint_code": checkpoint["code"],
                    "pillar_name": checkpoint["pillar_name"],
                    "evidence_quote": quote,
                    "reason": reason,
                })
            entries.append({"chunk_id": chunk["id"], "matches": matches})
        return {
            "success": True,
            "message": {"checkpoint_mapping_output": {"project_id": payload["project_id"], "chunk_results": entries}},
            "metainfo": {"prompt_tokens": 10, "completion_tokens": 20, "model": ["test-model"]},
        }

    monkeypatch.setattr(chunk_mapping_service, "call_helper_agent", _call)
    monkeypatch.setattr(chunk_mapping_service.time, "sleep", lambda seconds: None)
    return state


@pytest.fixture
def seeded(make_user):
    """A user, a project, one document with chunks, all waiting to be mapped."""
    alice = make_user("map-owner")
    response = alice.client.post("/api/projects", json={"name": "Mapping"})
    project_id = response.json()["id"]

    content_text = ""
    starts = []
    for text in CHUNK_TEXTS:
        starts.append(len(content_text))
        content_text += text + "\n\n"

    with get_session_factory()() as db:
        source = ContextSource(
            project_id=project_id, created_by=alice.id, title="Notes", original_filename="notes.txt",
            blob_path=f"tests/{uuid.uuid4().hex}.txt", mime_type="text/plain",
            file_size_bytes=len(content_text), processing_status="ready",
        )
        source.content = ContextContent(content_text=content_text, extraction_method="test")
        db.add(source)
        db.flush()
        content_id = source.content.id
        chunk_ids = []
        for number, (text, start) in enumerate(zip(CHUNK_TEXTS, starts), start=1):
            chunk = ContextChunk(
                context_content_id=content_id, chunk_number=number, chunk_text=text,
                start_char=start, end_char=start + len(text), char_count=len(text),
            )
            db.add(chunk)
            db.flush()
            chunk_ids.append(chunk.id)
        db.commit()
    return {"user": alice, "project_id": project_id, "content_id": content_id,
            "chunk_ids": chunk_ids, "content_text": content_text}


def _chunk_rows(chunk_ids):
    with get_session_factory()() as db:
        return {c.id: (c.mapping_status, c.mapping_attempts, c.mapping_error)
                for c in db.query(ContextChunk).filter(ContextChunk.id.in_(chunk_ids))}


def _active_mappings(project_id):
    with get_session_factory()() as db:
        return [(m.context_chunk_id, m.checkpoint_id) for m in
                db.query(ContextCheckpointMapping).filter(
                    ContextCheckpointMapping.project_id == project_id,
                    ContextCheckpointMapping.is_active == true(),
                )]


def test_job_maps_chunks_and_each_mapping_points_at_its_exact_quote(seeded, fake_agent):
    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])

    statuses = _chunk_rows(seeded["chunk_ids"])
    assert statuses[seeded["chunk_ids"][0]][0] == "MAPPED"
    assert statuses[seeded["chunk_ids"][1]][0] == "MAPPED"
    assert statuses[seeded["chunk_ids"][2]][0] == "MAPPED"
    assert statuses[seeded["chunk_ids"][3]][0] == "NO_MATCH"
    assert fake_agent["calls"] == 1  # four chunks fit in one batch of six

    with get_session_factory()() as db:
        evidence = db.query(MappingEvidence).join(ContextCheckpointMapping).filter(
            ContextCheckpointMapping.project_id == seeded["project_id"]).all()
        assert len(evidence) == 3
        for row in evidence:
            assert seeded["content_text"][row.evidence_start_char : row.evidence_end_char] == row.evidence_quote
        run = db.query(AgentRun).filter(AgentRun.project_id == seeded["project_id"]).one()
        assert run.status == "succeeded"
        assert run.chunk_count == 4
        assert run.model == "test-model"


def test_running_the_job_again_sends_nothing_and_adds_no_duplicates(seeded, fake_agent):
    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])
    first = sorted(_active_mappings(seeded["project_id"]))
    calls_after_first = fake_agent["calls"]

    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])

    assert fake_agent["calls"] == calls_after_first
    assert sorted(_active_mappings(seeded["project_id"])) == first


def test_a_chunk_whose_matches_are_all_invalid_ends_as_no_match(seeded, fake_agent):
    fake_agent["bad_quote_for"] = CHUNK_TEXTS[1]

    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])

    assert _chunk_rows(seeded["chunk_ids"])[seeded["chunk_ids"][1]][0] == "NO_MATCH"


def test_a_timeout_is_retried_three_times_then_the_chunks_fail(seeded, fake_agent):
    fake_agent["error"] = AgentTimeoutError("Agent5i did not answer within 180 seconds.")

    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])

    assert fake_agent["calls"] == 3
    status, attempts, error = _chunk_rows(seeded["chunk_ids"])[seeded["chunk_ids"][0]]
    assert status == "FAILED"
    assert attempts == 1
    assert "did not answer" in error
    assert _active_mappings(seeded["project_id"]) == []


def test_an_http_401_is_not_retried(seeded, fake_agent):
    fake_agent["error"] = AgentHttpError(401)

    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])

    assert fake_agent["calls"] == 1
    assert _chunk_rows(seeded["chunk_ids"])[seeded["chunk_ids"][0]][0] == "FAILED"


def test_chunks_already_mapped_are_not_sent_again_even_when_mixed_with_new_ones(seeded, fake_agent):
    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"][:2])
    calls = fake_agent["calls"]

    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])

    assert fake_agent["calls"] == calls + 1
    assert _chunk_rows(seeded["chunk_ids"])[seeded["chunk_ids"][3]][0] == "NO_MATCH"


def test_manual_retry_requeues_only_failed_chunks(seeded, fake_agent):
    fake_agent["error"] = AgentHttpError(503)
    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])
    fake_agent["error"] = None

    response = seeded["user"].client.post(f"/api/context-content/{seeded['content_id']}/chunks/map")

    assert response.status_code == 202
    assert response.json() == {"queued": 4}
    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])
    assert _chunk_rows(seeded["chunk_ids"])[seeded["chunk_ids"][0]][0] == "MAPPED"


def test_mapping_endpoints_return_the_saved_matches(seeded, fake_agent):
    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])

    by_content = seeded["user"].client.get(f"/api/context-content/{seeded['content_id']}/mappings").json()
    by_project = seeded["user"].client.get(
        f"/api/projects/{seeded['project_id']}/mappings", params={"checkpoint_code": "TECH04"}
    ).json()

    assert len(by_content) == 3
    assert {row["checkpoint_code"] for row in by_content} == {"TECH03", "TECH04", "TECH01"}
    assert all(row["pillar_name"] == "Tech Discovery" for row in by_content)
    assert len(by_project) == 1
    assert by_project[0]["checkpoint_code"] == "TECH04"
    assert by_project[0]["reason"] == "Documents shared warehouse credentials."


def test_another_user_gets_404_on_every_mapping_endpoint(seeded, fake_agent, make_user):
    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])
    bob = make_user("map-intruder")

    responses = [
        bob.client.get(f"/api/context-content/{seeded['content_id']}/mappings"),
        bob.client.get(f"/api/projects/{seeded['project_id']}/mappings"),
        bob.client.post(f"/api/context-content/{seeded['content_id']}/chunks/map"),
    ]

    assert [r.status_code for r in responses] == [404, 404, 404]


def test_a_mapping_endpoint_requires_sign_in(seeded):
    anonymous = TestClient(app)

    assert anonymous.get(f"/api/context-content/{seeded['content_id']}/mappings").status_code == 401


def test_creating_chunks_queues_exactly_the_new_chunk_ids(make_user, monkeypatch):
    queued = []
    monkeypatch.setattr(chunk_mapping_service, "enqueue_chunk_mapping",
                        lambda background, chunk_ids: queued.append(list(chunk_ids)))
    alice = make_user("map-trigger")
    project_id = alice.client.post("/api/projects", json={"name": "Trigger"}).json()["id"]
    text = " ".join(f"The team reviews item {n} in the workshop." for n in range(1, 40))
    with get_session_factory()() as db:
        source = ContextSource(
            project_id=project_id, created_by=alice.id, title="Notes", original_filename="notes.txt",
            blob_path=f"tests/{uuid.uuid4().hex}.txt", mime_type="text/plain",
            file_size_bytes=len(text), processing_status="ready",
        )
        source.content = ContextContent(content_text=text, extraction_method="test")
        db.add(source)
        db.commit()
        content_id = source.content.id

    response = alice.client.post(f"/api/context-content/{content_id}/chunks")

    assert response.status_code == 201
    created_ids = [chunk["id"] for chunk in response.json()]
    assert queued == [created_ids]


def test_a_project_with_mappings_can_still_be_deleted(seeded, fake_agent, make_user):
    chunk_mapping_service.run_mapping_job(seeded["chunk_ids"])
    assert _active_mappings(seeded["project_id"])

    response = seeded["user"].client.delete(f"/api/projects/{seeded['project_id']}")

    assert response.status_code == 204
    with get_session_factory()() as db:
        assert db.query(ContextCheckpointMapping).filter(
            ContextCheckpointMapping.project_id == seeded["project_id"]).count() == 0
