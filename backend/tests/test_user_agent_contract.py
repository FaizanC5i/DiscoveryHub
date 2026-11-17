import json

import pytest

from app.services.answers.user_agent import (
    ContractError,
    SentCheckpoint,
    final_output,
    parse_proposals,
)

CHUNK_A = 201
CHUNK_B = 202


def sent():
    return [
        SentCheckpoint(id=401, code="USER01", chunk_ids=frozenset({CHUNK_A, CHUNK_B}),
                       mapping_by_chunk={CHUNK_A: 1, CHUNK_B: 2}),
        SentCheckpoint(id=402, code="USER02", chunk_ids=frozenset({CHUNK_A}), mapping_by_chunk={CHUNK_A: 3}),
    ]


def item(code="USER01", cid=401, **overrides):
    base = {
        "checkpoint_id": cid,
        "checkpoint_code": code,
        "proposed_answer": "Store staff check the receipt.",
        "status": "Pending Approval",
        "is_completed": True,
        "completion_score": 0.9,
        "missing_information": [],
        "clarification_questions": [],
        "evidence": [{"chunk_id": str(CHUNK_A), "source_title": "x", "page_number": None,
                      "reason": "Describes the receipt check."}],
    }
    base.update(overrides)
    return base


def double_encoded(proposals):
    """The platform's real shape: message is a string whose chunk_results is another string."""
    return json.dumps({"chunk_results": json.dumps({"project_id": 1, "run_id": None, "proposals": proposals})})


def test_final_output_reads_double_encoded_message():
    output = final_output({"success": True, "message": double_encoded([item()])})
    assert output["proposals"][0]["checkpoint_code"] == "USER01"


def test_final_output_refuses_message_without_proposals():
    with pytest.raises(ContractError):
        final_output({"message": json.dumps({"other": 1})})


def test_valid_proposal_accepted_and_missing_checkpoint_reported():
    result = parse_proposals({"proposals": [item()]}, sent())
    assert 401 in result.accepted
    assert 402 in result.failures


def test_evidence_outside_sent_chunks_is_dropped_with_warning():
    bad = item(evidence=[{"chunk_id": "999", "reason": "x"}, {"chunk_id": str(CHUNK_A), "reason": "ok"}])
    result = parse_proposals({"proposals": [bad]}, sent())
    assert [e.chunk_id for e in result.accepted[401].evidence] == [CHUNK_A]
    assert any("999" in warning for warning in result.warnings)


def test_approved_status_from_agent_is_rejected():
    result = parse_proposals({"proposals": [item(status="Approved", is_completed=True)]}, sent())
    assert "Unsupported status" in result.failures[401]


def test_is_completed_must_match_status():
    result = parse_proposals({"proposals": [item(is_completed=False)]}, sent())
    assert "is_completed" in result.failures[401]


def test_pending_without_answer_is_rejected():
    result = parse_proposals({"proposals": [item(proposed_answer="   ")]}, sent())
    assert "needs an answer" in result.failures[401]


def test_needs_clarification_may_have_empty_answer():
    result = parse_proposals(
        {"proposals": [item(proposed_answer="", status="Needs Clarification",
                            is_completed=False, completion_score=0.0)]},
        sent(),
    )
    assert result.accepted[401].proposed_answer == ""


def test_checkpoint_id_mismatch_is_rejected():
    result = parse_proposals({"proposals": [item(cid=999)]}, sent())
    assert "checkpoint_id" in result.failures[401]


def test_unknown_code_is_ignored():
    result = parse_proposals({"proposals": [item(code="USR99")]}, sent())
    assert result.accepted == {}
    assert set(result.failures) == {401, 402}


def test_first_valid_proposal_wins_for_a_repeated_checkpoint():
    result = parse_proposals(
        {"proposals": [item(proposed_answer="First answer."), item(proposed_answer="Second answer.")]},
        sent(),
    )
    assert result.accepted[401].proposed_answer == "First answer."
    assert result.warnings