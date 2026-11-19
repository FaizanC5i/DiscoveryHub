# tests/test_checkpoint_answer_schema.py
"""
Schema checks for the checkpoint answer tables (migration 010). These check that the models
configure, that the database rejects invalid rows, and that deleting a project removes the whole
answer chain. No application logic is involved. Rows are created directly and cleaned up by the
project cascade.
Run from backend/: python -m pytest -q tests/test_checkpoint_answer_schema.py
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import configure_mappers

from app.db import models
from app.db.models import (
    Agent,
    AgentRun,
    CheckpointAnswerEvidence,
    CheckpointAnswerProposal,
    CheckpointAnswerVersion,
    ContextChunk,
    ContextCheckpointMapping,
    ContextContent,
    ContextSource,
    DiscoveryCheckpoint,
    MappingEvidence,
    ProjectCheckpointAnswer,
    Project,
    ProposalEvidence,
)
from app.db.session import get_session_factory

CHUNK_TEXT = "Warehouse supervisors check order status several times per shift."


def test_models_configure_and_self_reference_points_the_right_way():
    configure_mappers()

    relationship = CheckpointAnswerProposal.__mapper__.relationships["superseded_by"]

    assert relationship.direction.name == "MANYTOONE"
    assert [c.name for c in relationship.remote_side] == ["id"]


@pytest.fixture
def answer_setup(make_user):
    """A project with one chunk, one agent run and one mapping, ready for answer rows."""
    alice = make_user("answer-schema")
    project_id = alice.client.post("/api/projects", json={"name": "Answers"}).json()["id"]
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
        db.flush()
        helper_id = db.query(Agent.id).filter(Agent.agent_code == "HELPER_AGENT").scalar()
        checkpoint_id = db.query(DiscoveryCheckpoint.id).filter(DiscoveryCheckpoint.code == "TECH01").scalar()
        run = AgentRun(project_id=project_id, agent_id=helper_id, status="succeeded", chunk_count=1)
        db.add(run)
        db.flush()
        mapping = ContextCheckpointMapping(project_id=project_id, context_chunk_id=chunk.id,
                                           checkpoint_id=checkpoint_id, agent_run_id=run.id,
                                           mapped_by_agent_id=helper_id, is_active=True)
        mapping.evidence.append(MappingEvidence(evidence_quote=CHUNK_TEXT[:20], reason="Test.",
                                                evidence_start_char=0, evidence_end_char=20))
        db.add(mapping)
        db.commit()
        return {"user_id": alice.id, "project_id": project_id, "chunk_id": chunk.id,
                "run_id": run.id, "mapping_id": mapping.id, "checkpoint_id": checkpoint_id}


def _answer(setup, **overrides) -> ProjectCheckpointAnswer:
    values = {"project_id": setup["project_id"], "checkpoint_id": setup["checkpoint_id"], "status": "NOT_STARTED"}
    values.update(overrides)
    return ProjectCheckpointAnswer(**values)


def test_all_five_tables_exist_in_the_database():
    from sqlalchemy import inspect

    from app.db.session import get_engine

    tables = set(inspect(get_engine()).get_table_names())

    assert {"project_checkpoint_answers", "checkpoint_answer_proposals", "proposal_evidence",
            "checkpoint_answer_versions", "checkpoint_answer_evidence"} <= tables


def test_one_answer_per_checkpoint_per_project_is_enforced(answer_setup):
    with get_session_factory()() as db:
        db.add(_answer(answer_setup))
        db.commit()
        db.add(_answer(answer_setup))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()
        db.execute(delete(ProjectCheckpointAnswer).where(
            ProjectCheckpointAnswer.project_id == answer_setup["project_id"]))
        db.commit()


def test_completion_score_outside_zero_to_one_is_rejected(answer_setup):
    with get_session_factory()() as db:
        db.add(_answer(answer_setup, completion_score=Decimal("1.50")))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_a_version_number_below_one_is_rejected(answer_setup):
    with get_session_factory()() as db:
        answer = _answer(answer_setup)
        db.add(answer)
        db.flush()
        db.add(CheckpointAnswerVersion(checkpoint_answer_id=answer.id, version_number=0, answer_text="x",
                                       source="MANUAL", created_by=answer_setup["user_id"]))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_an_ai_proposal_version_without_a_proposal_is_rejected(answer_setup):
    with get_session_factory()() as db:
        answer = _answer(answer_setup)
        db.add(answer)
        db.flush()
        db.add(CheckpointAnswerVersion(checkpoint_answer_id=answer.id, version_number=1, answer_text="x",
                                       source="AI_PROPOSAL", proposal_id=None,
                                       created_by=answer_setup["user_id"]))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_the_same_chunk_cannot_be_linked_twice_to_one_version(answer_setup):
    with get_session_factory()() as db:
        answer = _answer(answer_setup)
        db.add(answer)
        db.flush()
        version = CheckpointAnswerVersion(checkpoint_answer_id=answer.id, version_number=1, answer_text="x",
                                          source="MANUAL", created_by=answer_setup["user_id"])
        db.add(version)
        db.flush()
        db.add(CheckpointAnswerEvidence(checkpoint_answer_id=answer.id, answer_version_id=version.id,
                                        context_chunk_id=answer_setup["chunk_id"]))
        db.add(CheckpointAnswerEvidence(checkpoint_answer_id=answer.id, answer_version_id=version.id,
                                        context_chunk_id=answer_setup["chunk_id"]))
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


def test_deleting_a_project_removes_its_whole_answer_chain(answer_setup):
    with get_session_factory()() as db:
        answer = _answer(answer_setup)
        db.add(answer)
        db.flush()
        proposal = CheckpointAnswerProposal(current_answer_id=answer.id, agent_run_id=answer_setup["run_id"],
                                            base_version_number=0, proposed_answer="Draft")
        db.add(proposal)
        db.flush()
        db.add(ProposalEvidence(proposal_id=proposal.id, context_chunk_id=answer_setup["chunk_id"],
                        mapping_id=answer_setup["mapping_id"]))
        version = CheckpointAnswerVersion(checkpoint_answer_id=answer.id, version_number=1, answer_text="Draft",
                                          source="AI_PROPOSAL", proposal_id=proposal.id,
                                          created_by=answer_setup["user_id"])
        db.add(version)
        db.flush()
        db.add(CheckpointAnswerEvidence(checkpoint_answer_id=answer.id, answer_version_id=version.id,
                                        context_chunk_id=answer_setup["chunk_id"]))
        db.commit()

        db.execute(delete(Project).where(Project.id == answer_setup["project_id"]))
        db.commit()

        assert db.scalar(select(ProjectCheckpointAnswer.id).where(
            ProjectCheckpointAnswer.project_id == answer_setup["project_id"])) is None
        assert db.scalar(select(CheckpointAnswerProposal.id).where(
            CheckpointAnswerProposal.current_answer_id == answer.id)) is None
        assert db.scalar(select(ProposalEvidence.id).where(ProposalEvidence.proposal_id == proposal.id)) is None
        assert db.scalar(select(CheckpointAnswerVersion.id).where(
            CheckpointAnswerVersion.checkpoint_answer_id == answer.id)) is None
        assert db.scalar(select(CheckpointAnswerEvidence.id).where(
            CheckpointAnswerEvidence.checkpoint_answer_id == answer.id)) is None


def test_deleting_an_answer_keeps_its_chunks_and_mappings(answer_setup):
    with get_session_factory()() as db:
        answer = _answer(answer_setup)
        db.add(answer)
        db.flush()
        proposal = CheckpointAnswerProposal(current_answer_id=answer.id, agent_run_id=answer_setup["run_id"],
                                            base_version_number=0, proposed_answer="Draft")
        db.add(proposal)
        db.flush()
        db.add(ProposalEvidence(proposal_id=proposal.id, context_chunk_id=answer_setup["chunk_id"],
                        mapping_id=answer_setup["mapping_id"]))
        db.commit()

        db.execute(delete(ProjectCheckpointAnswer).where(ProjectCheckpointAnswer.id == answer.id))
        db.commit()

        assert db.scalar(select(ProposalEvidence.id).where(ProposalEvidence.proposal_id == proposal.id)) is None
        assert db.get(ContextChunk, answer_setup["chunk_id"]) is not None
        assert db.get(ContextCheckpointMapping, answer_setup["mapping_id"]) is not None

