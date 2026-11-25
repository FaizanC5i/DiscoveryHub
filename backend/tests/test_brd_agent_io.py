"""BRD agent input and reply handling (pure functions, no database or network)."""

import json

import pytest

from app.services import brd_agent_io as io

KEYS = ["business_objectives", "scope", "risks"]

ANSWERS = [
    {"code": "USER05", "name": "Stakeholders", "pillar": "User", "question": "Who are the stakeholders?",
     "answer": "  Ops lead, CFO and 3 regional managers.  "},
    {"code": "TECH02", "name": "Integrations", "pillar": "Tech", "question": "Which systems connect?",
     "answer": "Salesforce via REST, nightly."},
]


def test_source_text_lists_every_approved_answer_with_its_checkpoint_and_question():
    text = io.build_source_text(ANSWERS)
    assert text.startswith("APPROVED DISCOVERY ANSWERS")
    assert "--- CHECKPOINT USER05: Stakeholders (User pillar) ---" in text
    assert "Question: Who are the stakeholders?" in text
    assert "Approved answer:\nOps lead, CFO and 3 regional managers." in text
    assert text.index("USER05") < text.index("TECH02")


def test_source_text_says_so_when_nothing_is_approved():
    assert "No approved answers are available" in io.build_source_text([])


def test_agent_input_keeps_the_control_block_format_and_puts_the_answers_after_it():
    text = io.build_agent_input("SOURCE", io.MODE_REGENERATE_SECTION, "scope", "Q1: a\nA1: b", "old text")
    assert text == (
        "AGENT_REQUEST\nmode: regenerate_section\ntarget_section: scope\n"
        "clarification:\nQ1: a\nA1: b\ncurrent_section_content:\nold text\n"
        "END_AGENT_REQUEST\n\nORIGINAL_SOURCE_DOCUMENT:\nSOURCE"
    )


def test_clarifications_are_numbered_question_answer_pairs():
    assert io.format_clarifications([("Why?", " Because. "), ("When?", "Q3")]) == (
        "Q1: Why?\nA1: Because.\n\nQ2: When?\nA2: Q3"
    )


def test_reply_wrapped_in_a_json_string_is_found_and_every_section_is_filled_in():
    inner = {
        "mode": "generate_all",
        "sections": {
            "business_objectives": {"status": "complete", "content": "- Cut costs\\n- Faster close"},
            "scope": {"status": "insufficient", "message": "", "questions": ["What is in?", "", "And out?"]},
        },
    }
    raw = {"output": "```json\n" + json.dumps(inner) + "\n```"}
    result = io.normalize_agent_response(raw, KEYS, io.MODE_GENERATE_ALL)

    assert result["sections"]["business_objectives"] == {
        "status": "complete", "content": "- Cut costs\n- Faster close", "message": "", "questions": []
    }
    assert result["sections"]["scope"]["status"] == "insufficient"
    assert result["sections"]["scope"]["message"] == io.NO_CONTENT_MSG
    assert result["sections"]["scope"]["questions"] == ["What is in?", "And out?"]
    # A section the agent left out is reported as insufficient, never dropped.
    assert result["sections"]["risks"]["status"] == "insufficient"


def test_complete_without_content_is_insufficient_and_skipped_counts_only_for_single_sections():
    raw = {"sections": {"scope": {"status": "complete", "content": "  "}, "risks": {"status": "skipped"}}}
    all_mode = io.normalize_agent_response(raw, KEYS, io.MODE_GENERATE_ALL)
    assert all_mode["sections"]["scope"]["status"] == "insufficient"
    assert all_mode["sections"]["risks"]["status"] == "insufficient"

    one = io.normalize_agent_response(raw, KEYS, io.MODE_REGENERATE_SECTION, "scope")
    assert one["sections"]["risks"]["status"] == "skipped"


def test_questions_only_reply_is_accepted_and_capped_at_three():
    raw = "Here you go: " + json.dumps({"questions": ["a", "b", "c", "d"]})
    result = io.normalize_agent_response(raw, KEYS, io.MODE_CLARIFY_QUESTIONS, "scope")
    assert result["questions"] == ["a", "b", "c"]


def test_long_reply_with_an_earlier_insufficient_object_keeps_the_richest_one():
    keys = ["business_objectives", "scope"]
    early = {"mode": "generate_all", "sections": {k: {"status": "insufficient"} for k in keys}}
    final = {
        "mode": "generate_all",
        "sections": {
            "business_objectives": {"status": "complete", "content": "Reduce booking delays by half."},
            "scope": {"status": "complete", "content": "Participant booking and reporting."},
        },
    }
    reply = {"messages": [{"content": json.dumps(early)}, {"content": json.dumps(final)}]}
    result = io.normalize_agent_response(reply, keys, io.MODE_GENERATE_ALL)
    assert result["sections"]["business_objectives"]["status"] == "complete"
    assert result["sections"]["scope"]["content"] == "Participant booking and reporting."


def test_reply_without_the_brd_object_raises():
    with pytest.raises(io.AgentReplyError):
        io.normalize_agent_response({"output": "sorry, I cannot help"}, KEYS, io.MODE_GENERATE_ALL)


def test_refresh_puts_new_answers_first_and_marks_them_as_priority():
    new, old = ANSWERS[1:], ANSWERS[:1]
    text = io.build_refresh_source_text(new, old)
    assert text.startswith("APPROVED DISCOVERY ANSWERS\n\nNEW OR UPDATED ANSWERS")
    assert "HIGHEST PRIORITY" in text
    assert text.index("TECH02") < text.index("OTHER APPROVED ANSWERS") < text.index("USER05")


def test_refresh_without_new_answers_is_the_normal_list():
    assert io.build_refresh_source_text([], ANSWERS) == io.build_source_text(ANSWERS)
