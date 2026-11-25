"""PRD agent request and reply: the format of the PRD agent builder's app."""

import json

import pytest

from app.services import prd_agent_io as prd_io

NUMBERS = {3: "problem_objectives", 4: "target_users_personas", 5: "product_scope"}


def _definition(n: int, key: str) -> dict:
    prompt = json.dumps({"key_contents": "Problem definition", "required_details": ["Problem definition"]})
    return prd_io.section_definition(n, key, "Problem Statement & Objectives", prompt)


def test_section_definition_reads_the_stored_prompt():
    d = _definition(3, "problem_objectives")
    assert d["id"] == 3 and d["code"] == "PRDS03" and d["title"] == d["name"]
    assert d["key_contents"] == "Problem definition" and d["required_details"] == ["Problem definition"]


def test_payload_has_the_agent_fields_and_no_internal_key():
    user = prd_io.user_answers([{"code": "USR-01", "name": "Problem", "question": "Q?", "answer": " A "}])
    tech = prd_io.tech_answers([{"code": "PRDCP01", "name": "Frontend", "question": "Q?", "answer": "B", "checkpoint_id": 9}])
    payload = prd_io.build_payload(
        prd_io.ACTION_GENERATE, [_definition(3, "problem_objectives")], user, tech, [],
        project_id=1, run_id=2, settings={"title": "T", "audience": "", "scope": ""}, new_answer_codes=["USR-01"],
    )
    for field in ("revision_instruction", "action", "instructions", "approved_user_discovery", "prd_checkpoints",
                  "prd_sections", "existing_sections", "clarifications", "target_section_id"):
        assert field in payload
    assert payload["approved_user_discovery"][0] == {
        "checkpoint_code": "USR-01", "name": "Problem", "question": "Q?", "approved_answer": "A", "evidence": []}
    assert payload["prd_checkpoints"][0]["is_approved"] is True and payload["prd_checkpoints"][0]["id"] == 9
    assert "key" not in payload["prd_sections"][0]
    assert payload["new_or_updated_answers"] == ["USR-01"] and "HIGHEST PRIORITY" in payload["revision_instruction"]
    assert payload["document_settings"]["title"] == "T"


def test_reply_wrapped_by_agent5i_is_read():
    inner = {"sections": [
        {"section_id": 3, "proposed_answer": "## Problem\nSlow orders.", "missing_information": [],
         "clarification_questions": []},
        {"section_id": "4", "proposed_answer": "", "missing_information": ["No personas"],
         "clarification_questions": ["Who?", "Why?", "When?", "Extra?"]},
        {"section_id": 99, "proposed_answer": "not asked for"},
    ]}
    raw = {"outputs": [{"name": "prd_output", "value": "Here you go:\n```json\n" + json.dumps(inner) + "\n```"}]}
    out = prd_io.normalize_reply(raw, NUMBERS)
    assert out["problem_objectives"] == {"status": "complete", "content": "## Problem\nSlow orders.", "message": "",
                                         "questions": []}
    assert out["target_users_personas"]["status"] == "insufficient"
    assert out["target_users_personas"]["questions"] == ["Who?", "Why?", "When?"]
    assert out["target_users_personas"]["message"] == "No personas"
    assert "product_scope" not in out and len(out) == 2


def test_partial_section_keeps_text_and_questions():
    raw = {"sections": [{"id": "PRDS05", "proposed_answer": "In scope: dashboard.",
                         "missing_information": ["Out of scope unknown"], "clarification_questions": ["What is out?"]}]}
    out = prd_io.normalize_reply(raw, NUMBERS)
    assert out["product_scope"]["status"] == "complete" and out["product_scope"]["questions"] == ["What is out?"]


def test_single_section_object_without_array_is_read():
    out = prd_io.normalize_reply({"result": {"section_id": 3, "proposed_answer": "Text"}}, NUMBERS)
    assert out["problem_objectives"]["content"] == "Text"


def test_reply_without_sections_is_an_error():
    with pytest.raises(prd_io.PrdReplyError):
        prd_io.normalize_reply({"message": "I could not do it"}, NUMBERS)
