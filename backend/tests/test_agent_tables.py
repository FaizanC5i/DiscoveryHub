# tests/test_agent_tables.py
"""
Checks for the agent tables after migration 009: seeded agents, uniqueness rules, and what a
Helper run writes. Runs against the real database; every row it creates is removed afterwards.
Run from backend/: python -m pytest -q tests/test_agent_tables.py
"""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from app.db.models import (
    Agent,
    AgentRun,
    AgentRunChunk,
    AgentRunCheckpoint,
    ContextChunk,
    ContextContent,
    ContextSource,
    DiscoveryCheckpoint,
)
from app.db.session import get_session_factory
from app.services import chunk_mapping_service

CHUNK_TEXT = "Warehouse supervisors check order status several times per shift."


@pytest.fixture
def project_and_chunk(make_user):
    alice = make_user("agent-tables")
    project_id = alice.client.post("/api/projects", json={"name": "Agent tables"}).json()["id"]
    with get_session_factory()() as db:
        source = ContextSource(
            project_id=project_id, created_by=alice.id, title="Notes", original_filename="notes.txt",
            blob_path=f"tests/{uuid.uuid4().hex}.txt", mime_type="text/plain",
            file_size_bytes=len(CHUNK_TEXT), processing_status="ready",
        )
        source.content = ContextContent(content_text=CHUNK_TEXT, extraction_method="test")
        db.add(source)
        db.flush()
        chunk = ContextChunk(context_content_id=source.content.id, chunk_number=1, chunk_text=CHUNK_TEXT,
                             start_char=0, end_char=len(CHUNK_TEXT), char_count=len(CHUNK_TEXT))
        db.add(chunk)
        db.commit()
        return {"project_id": project_id, "chunk_id": chunk.id, "source_id": source.id}


def test_the_pillar_agents_and_the_helper_agent_are_seeded():
    with get_session_factory()() as db:
        rows = {a.agent_code: a for a in db.query(Agent).all()}

    assert rows["HELPER_AGENT"].pillar_id is None
    assert rows["USER_AGENT"].pillar_id is not None
    assert rows["DATA_AGENT"].pillar_id is not None
    assert rows["TECH_AGENT"].pillar_id is not None
    assert len({rows[c].pillar_id for c in ("USER_AGENT", "DATA_AGENT", "TECH_AGENT")}) == 3


def test_a_second_agent_for_the_same_pillar_is_rejected():
    with get_session_factory()() as db:
        pillar_id = db.query(Agent.pillar_id).filter(Agent.agent_code == "USER_AGENT").scalar()
        db.add(Agent(agent_code=f"DUP_{uuid.uuid4().hex[:6]}", name="Duplicate", pillar_id=pillar_id))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_two_helper_style_agents_without_a_pillar_are_allowed():
    codes = [f"HELPER_TEST_{uuid.uuid4().hex[:6]}", f"HELPER_TEST_{uuid.uuid4().hex[:6]}"]
    with get_session_factory()() as db:
        for code in codes:
            db.add(Agent(agent_code=code, name="Test helper", pillar_id=None))
        db.commit()
        db.query(Agent).filter(Agent.agent_code.in_(codes)).delete(synchronize_session=False)
        db.commit()


def test_the_same_chunk_cannot_be_sent_twice_to_one_run(project_and_chunk):
    with get_session_factory()() as db:
        helper_id = db.query(Agent.id).filter(Agent.agent_code == "HELPER_AGENT").scalar()
        run = AgentRun(project_id=project_and_chunk["project_id"], agent_id=helper_id,
                       status="running", chunk_count=1)
        db.add(run)
        db.flush()
        db.add(AgentRunChunk(agent_run_id=run.id, context_chunk_id=project_and_chunk["chunk_id"]))
        db.add(AgentRunChunk(agent_run_id=run.id, context_chunk_id=project_and_chunk["chunk_id"]))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_the_same_checkpoint_cannot_be_recorded_twice_for_one_run(project_and_chunk):
    with get_session_factory()() as db:
        run = AgentRun(project_id=project_and_chunk["project_id"], status="running", chunk_count=1)
        db.add(run)
        db.flush()
        checkpoint_id = db.query(DiscoveryCheckpoint.id).filter(DiscoveryCheckpoint.code == "TECH01").scalar()
        db.add(AgentRunCheckpoint(agent_run_id=run.id, checkpoint_id=checkpoint_id, status="PENDING"))
        db.add(AgentRunCheckpoint(agent_run_id=run.id, checkpoint_id=checkpoint_id, status="PENDING"))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_a_helper_run_records_its_agent_and_batch_and_nothing_in_the_per_checkpoint_tables(
    project_and_chunk, monkeypatch
):
    def _reply(payload):
        return {"message": {"checkpoint_mapping_output": {"project_id": payload["project_id"], "chunk_results": [
            {"chunk_id": payload["context_chunks"][0]["id"], "matches": []}]}}}

    monkeypatch.setattr(chunk_mapping_service, "call_helper_agent", _reply)

    chunk_mapping_service.run_mapping_job([project_and_chunk["chunk_id"]])

    with get_session_factory()() as db:
        helper_id = db.query(Agent.id).filter(Agent.agent_code == "HELPER_AGENT").scalar()
        run = (db.query(AgentRun).filter(AgentRun.project_id == project_and_chunk["project_id"])
               .order_by(AgentRun.id.desc()).first())
        assert run.agent_id == helper_id
        assert run.batch_id.startswith("BATCH-")
        assert run.status == "succeeded"
        assert db.query(AgentRunCheckpoint).filter(AgentRunCheckpoint.agent_run_id == run.id).count() == 0
        assert db.query(AgentRunChunk).filter(AgentRunChunk.agent_run_id == run.id).count() == 0
