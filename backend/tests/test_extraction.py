import io

import pytest
from docx import Document

from app.core.file_types import ALLOWED_KINDS
from app.services.extraction.extractors import ExtractionError, extract_text


def _docx_with_table() -> bytes:
    document = Document()
    document.add_paragraph("Project scope")
    table = document.add_table(rows=2, cols=2)
    table.cell(0, 0).text = "Name"
    table.cell(0, 1).text = "Owner"
    table.cell(1, 0).text = "Atlas"
    table.cell(1, 1).text = "Alex"
    buffer = io.BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_docx_paragraphs_and_tables_are_extracted():
    result = extract_text(ALLOWED_KINDS[".docx"], _docx_with_table())

    assert "Project scope" in result.text
    assert "Name | Owner" in result.text
    assert "Atlas | Alex" in result.text


def test_plain_text_is_extracted():
    result = extract_text(ALLOWED_KINDS[".txt"], "Hello discovery".encode("utf-8"))

    assert result.text == "Hello discovery"


def test_empty_docx_reports_no_text():
    buffer = io.BytesIO()
    Document().save(buffer)

    with pytest.raises(ExtractionError, match="No text"):
        extract_text(ALLOWED_KINDS[".docx"], buffer.getvalue())


def test_scanned_pdf_is_rejected_with_a_clear_message():
    # A PDF with no text layer. Built from a blank page, so there is nothing to extract.
    blank_pdf = (
        b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n"
        b"2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n"
        b"3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 200 200]>>endobj\n"
        b"trailer<</Root 1 0 R>>\n%%EOF"
    )

    with pytest.raises(ExtractionError, match="No text was found"):
        extract_text(ALLOWED_KINDS[".pdf"], blank_pdf)