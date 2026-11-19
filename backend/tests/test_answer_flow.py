import json
import uuid

import pytest
from sqlalchemy import select

from app.db.models import (
    Agent,
    AgentRun,
    CheckpointAnswerEvidence,
    CheckpointAnswerProposal,
    CheckpointAnswerVersion,
    ContextCheckpointMapping,
    ContextChunk,
    ContextContent,
    ContextSource,
    MappingEvidence,
    Project,
    ProjectCheckpointAnswer,
    ProposalEvidence,
)
from app.db.session import get_session_factory
from app.services.answers import answer_pipeline
from app.services.answers.answer_pipeline import execute_run
from app.services.answers.answer_review import approve_proposal, build_overview
from app.services.answers.common import ReviewError
from app.services.answers.user_agent import AgentCallError

CHECKPOINT_ID = 401  # USER01, Persona and Roles
TEXT = "Store associates check the receipt and confirm the item condition before they offer a refund."
QUOTE = "Store associates check the receipt"


def seed(owner_id: int) -> int:
    with get_session_factory()() as db:
        helper_id = db.scalar(select(Agent.id).where(Agent.agent_code == "HELPER_AGENT"))
        project = Project(name="Answer flow", owner_id=owner_id)
        db.add(project)
        db.flush()
        source = ContextSource(
            project_id=project.id,
            created_by=owner_id,
            source_type="FILE_UPLOAD",
            title="returns",
            original_filename="returns.txt",
            blob_path=f"test/{uuid.uuid4().hex}.txt",
            mime_type="text/plain",
            file_size_bytes=len(TEXT),
            processing_status="ready",
        )
        db.add(source)
        db.flush()
        content = ContextContent(context_source_id=source.id, content_text=TEXT, extraction_method="test")
        db.add(content)
        db.flush()
        chunk = ContextChunk(
            context_content_id=content.id,
            chunk_number=1,
            chunk_text=TEXT,
            start_char=0,
            end_char=len(TEXT),
            char_count=len(TEXT),
            mapping_status="MAPPED",
        )
        db.add(chunk)
        db.flush()
        run = AgentRun(project_id=project.id, agent_id=helper_id, run_type="checkpoint_mapping",
                       status="succeeded", chunk_count=1)
        db.add(run)
        db.flush()
        mapping = ContextCheckpointMapping(
            project_id=project.id,
            context_chunk_id=chunk.id,
            checkpoint_id=CHECKPOINT_ID,
            agent_run_id=run.id,
            mapped_by_agent_id=helper_id,
            is_active=True,
        )
        db.add(mapping)
        db.flush()
        db.add(MappingEvidence(mapping_id=mapping.id, evidence_quote=QUOTE, reason="Describes the role.",
                               evidence_start_char=0, evidence_end_char=len(QUOTE)))
        db.commit()
        return project.id


def double_encoded(proposals):
    return json.dumps({"chunk_results": json.dumps({"project_id": 1, "run_id": None, "proposals": proposals})})

def proposal_for(outcome, code="USER01"):
    return next(p["proposal_id"] for p in outcome.processed if p["checkpoint_code"] == code)

def fake_agent(answer="Store staff check receipts and item condition.", status="Pending Approval"):
    def call(batch):
        proposals = []
        for entry in batch["checkpoints"]:
            cp = entry["checkpoint"]
            target = cp["id"] == CHECKPOINT_ID
            text = answer if target else ""
            state = status if target else "Needs Clarification"
            evidence = (
                [{"chunk_id": str(cid), "reason": "Describes the receipt check."} for cid in entry["chunk_ids"][:1]]
                if target else []
            )
            proposals.append({
                "checkpoint_id": cp["id"],
                "checkpoint_code": cp["code"],
                "checkpoint_name": cp["name"],
                "question": cp["question"],
                "proposed_answer": text,
                "status": state,
                "is_completed": state == "Pending Approval",
                "completion_score": 0.8 if target else 0.0,
                "missing_information": [],
                "clarification_questions": [],
                "evidence": evidence,
            })
        return {"success": True, "message": double_encoded(proposals)}
    return call

def run_once(project_id, agent_call):
    with get_session_factory()() as db:
        return execute_run(db, project_id, [CHECKPOINT_ID], agent_call=agent_call)


def test_run_stores_pending_proposal_with_evidence(make_user):
    owner = make_user("flow-run")
    project_id = seed(owner.id)

    outcome = run_once(project_id, fake_agent())

    assert outcome.status == "succeeded"
    assert len(outcome.processed) == 19
    with get_session_factory()() as db:
        proposal = db.get(CheckpointAnswerProposal, proposal_for(outcome))
        assert proposal.status == "PENDING"
        assert proposal.agent_status == "Pending Approval"
        assert proposal.base_version_number == 0
        assert proposal.agent_run_id == outcome.run_id
        links = db.scalars(select(ProposalEvidence).where(ProposalEvidence.proposal_id == proposal.id)).all()
        assert len(links) == 1
        answer = db.get(ProjectCheckpointAnswer, proposal.current_answer_id)
        assert answer.status == "PENDING_REVIEW"
        run = db.get(AgentRun, outcome.run_id)
        assert run.status == "succeeded"
        assert run.raw_output


def test_regenerate_supersedes_previous_pending_proposal(make_user):
    owner = make_user("flow-regen")
    project_id = seed(owner.id)

    first = run_once(project_id, fake_agent("First draft of the answer."))
    second = run_once(project_id, fake_agent("Second draft of the answer."))

    with get_session_factory()() as db:
        old = db.get(CheckpointAnswerProposal, proposal_for(first))
        new = db.get(CheckpointAnswerProposal, proposal_for(second))
        assert old.status == "SUPERSEDED"
        assert old.superseded_by_proposal_id == new.id
        assert new.status == "PENDING"


def test_approval_writes_version_answer_and_evidence(make_user):
    owner = make_user("flow-approve")
    project_id = seed(owner.id)
    proposal_id = proposal_for(run_once(project_id, fake_agent()))

    with get_session_factory()() as db:
        result = approve_proposal(db, owner.id, project_id, proposal_id)

    assert result["version_number"] == 1
    with get_session_factory()() as db:
        answer = db.scalar(select(ProjectCheckpointAnswer).where(ProjectCheckpointAnswer.project_id == project_id))
        assert answer.status == "APPROVED"
        assert answer.current_answer == "Store staff check receipts and item condition."
        assert answer.approved_by == owner.id
        assert answer.is_completed is True
        assert len(db.scalars(select(CheckpointAnswerVersion)).all()) == 1
        assert len(db.scalars(select(CheckpointAnswerEvidence)).all()) == 1


def test_approving_twice_is_refused(make_user):
    owner = make_user("flow-twice")
    project_id = seed(owner.id)
    proposal_id = proposal_for(run_once(project_id, fake_agent()))

    with get_session_factory()() as db:
        approve_proposal(db, owner.id, project_id, proposal_id)

    with get_session_factory()() as db, pytest.raises(ReviewError) as refused:
        approve_proposal(db, owner.id, project_id, proposal_id)
    assert refused.value.status_code == 409


def test_non_owner_cannot_approve(make_user):
    owner = make_user("flow-owner")
    other = make_user("flow-other")
    project_id = seed(owner.id)
    proposal_id = proposal_for(run_once(project_id, fake_agent()))

    with get_session_factory()() as db, pytest.raises(ReviewError) as refused:
        approve_proposal(db, other.id, project_id, proposal_id)
    assert refused.value.status_code == 404


def test_agent_failure_records_failed_run_and_stores_nothing(make_user):
    owner = make_user("flow-fail")
    project_id = seed(owner.id)

    def failing(batch):
        raise AgentCallError("Agent5i returned HTTP 500.")

    outcome = run_once(project_id, failing)

    assert outcome.status == "failed"
    with get_session_factory()() as db:
        run = db.get(AgentRun, outcome.run_id)
        assert run.status == "failed"
        assert "HTTP 500" in run.error_message
        assert db.scalars(select(CheckpointAnswerProposal)).all() == []


def test_empty_clarification_answer_is_stored_but_cannot_be_approved(make_user):
    owner = make_user("flow-empty")
    project_id = seed(owner.id)
    outcome = run_once(
        project_id,
        fake_agent(answer="", status="Needs Clarification"),
    )
    assert outcome.status == "succeeded"
    proposal_id = proposal_for(outcome)

    with get_session_factory()() as db, pytest.raises(ReviewError) as refused:
        approve_proposal(db, owner.id, project_id, proposal_id)
    assert refused.value.code == "NO_ANSWER_TO_APPROVE"


def test_unexpected_error_while_storing_marks_run_failed(make_user, monkeypatch):
    owner = make_user("flow-crash")
    project_id = seed(owner.id)

    def boom(*args, **kwargs):
        raise RuntimeError("disk on fire")

    monkeypatch.setattr(answer_pipeline, "_store_proposal", boom)
    outcome = run_once(project_id, fake_agent())

    assert outcome.status == "failed"
    with get_session_factory()() as db:
        assert db.get(AgentRun, outcome.run_id).status == "failed"
        assert db.scalars(select(CheckpointAnswerProposal)).all() == []


def test_overview_shows_pending_proposal_and_evidence(make_user):
    owner = make_user("flow-overview")
    project_id = seed(owner.id)
    run_once(project_id, fake_agent())

    with get_session_factory()() as db:
        overview = build_overview(db, project_id)

    card = next(c for c in overview["checkpoints"] if c["checkpoint"]["id"] == CHECKPOINT_ID)
    assert card["pending_proposal"] is not None
    assert card["pending_proposal"]["evidence"][0]["reason"] == "Describes the receipt check."
    assert card["chunk_count"] == 1