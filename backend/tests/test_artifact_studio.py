"""Artifact Studio shaping: bullets, section mapping, settings sent to the agent, exports (no database)."""

import io
from datetime import datetime

from docx import Document

from app.services import artifact_studio_service as studio
from app.services import brd_agent_io


def test_markdown_lists_tables_and_headings_become_plain_bullets():
    md = (
        "#### Returns\n\n"
        "- **Unified view** for store staff\n"
        "1. Refunds above $150 need approval\n\n"
        "| Role | Responsibility |\n| --- | --- |\n| Store Associates | Handle returns |\n\n"
        "Plain sentence."
    )
    assert studio.markdown_to_bullets(md) == [
        "Returns",
        "Unified view for store staff",
        "Refunds above $150 need approval",
        "Store Associates – Handle returns",
        "Plain sentence.",
    ]
    assert studio.markdown_to_bullets(None) == []


def test_bullets_round_trip_to_markdown():
    assert studio.bullets_to_markdown(["One", " ", "Two "]) == "- One\n- Two"
    assert studio.markdown_to_bullets(studio.bullets_to_markdown(["One", "Two"])) == ["One", "Two"]


def _section(**over):
    base = {"section_key": "scope", "sort_order": 4, "title": "Scope", "status": "NOT_STARTED", "content": None, "open_proposal": None}
    base.update(over)
    return base


def test_a_draft_waiting_for_review_is_shown_first():
    s = studio._draft_section(_section(
        status="APPROVED", content="- old",
        open_proposal={"id": 9, "status": "PENDING", "content": "- new", "missing_reason": None, "questions": []},
    ))
    assert s == {"id": "scope", "number": 4, "title": "Scope", "status": "PENDING_REVIEW", "bullets": ["new"], "proposalId": 9}


def test_questions_are_shown_only_when_there_is_no_content():
    questions = {"id": 3, "status": "NEEDS_CLARIFICATION", "content": None, "missing_reason": None, "questions": ["What is in?"]}
    empty = studio._draft_section(_section(status="NEEDS_CLARIFICATION", open_proposal=questions))
    assert empty["status"] == "NEEDS_CLARIFICATION" and empty["bullets"] == []
    assert empty["missingReason"] == studio.DEFAULT_MISSING_REASON
    assert empty["clarificationQuestions"] == ["What is in?"]

    approved = studio._draft_section(_section(status="APPROVED", content="- In: EU", open_proposal=questions))
    assert approved["status"] == "APPROVED" and approved["bullets"] == ["In: EU"]
    assert studio._draft_section(_section())["status"] == "NOT_STARTED"


def test_draft_settings_are_sent_before_the_answers():
    text = brd_agent_io.build_document_settings("Claims Intake: BRD", "Executive sponsor", "")
    assert text == "DOCUMENT SETTINGS\nDocument title: Claims Intake: BRD\nAudience: Executive sponsor (write for this reader)\n\n"
    assert brd_agent_io.build_document_settings(None, None, None) == ""


def test_version_label():
    assert studio._version_label(datetime(2026, 11, 18, 17, 49)) == "Nov 18, 5:49 PM UTC"
    assert studio._version_label(datetime(2026, 11, 5, 0, 5)) == "Nov 5, 12:05 AM UTC"


DOC = {
    "title": "Claims Intake: Business Requirements Document",
    "description": "Discovery for claims intake",
    "warning": "Incomplete draft: discovery is not complete. Not client-ready.",
    "settings": ["Audience: Executive sponsor"],
    "sections": [
        {"heading": "01 Business Objectives", "bullets": ["Register claims the same day – 1 day target €"], "note": None, "questions": []},
        {"heading": "02 Users & Stakeholders", "bullets": [], "note": "No approved answer.", "questions": ["Who is the sponsor?"]},
    ],
    "sources": ["Kickoff notes"],
    "snapshot": {},
}


def test_markdown_export():
    md = studio._export_md(DOC)
    assert md.startswith("# Claims Intake: Business Requirements Document\n")
    assert "## 01 Business Objectives\n\n- Register claims the same day" in md
    assert "_No approved answer._" in md and "**Open questions**\n\n- Who is the sponsor?" in md
    assert "**Sources**\n\n- Kickoff notes" in md


def test_word_export_opens_and_has_the_sections():
    word = Document(io.BytesIO(studio._export_docx(DOC)))
    text = "\n".join(p.text for p in word.paragraphs)
    assert "01 Business Objectives" in text and "Who is the sponsor?" in text and "Kickoff notes" in text


def test_pdf_export_is_a_pdf_even_with_non_latin_characters():
    pdf = studio._export_pdf(DOC)
    assert pdf.startswith(b"%PDF") and len(pdf) > 500
