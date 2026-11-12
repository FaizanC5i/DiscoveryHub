"""
Text and table extraction using only Python packages.

- DOCX: python-docx reads paragraphs and tables.
- PDF: pdfplumber reads text and tables. Scanned PDFs with no text layer are rejected.
- TXT and Markdown: decoded as UTF-8.

Problems the user can fix raise ExtractionError, and the message is shown in the UI.
"""

import io
from dataclasses import dataclass

import pdfplumber
from docx import Document

from app.core.file_types import FileKind


class ExtractionError(Exception):
    """Extraction could not produce text. The message is safe to show to the user."""


@dataclass(frozen=True)
class Extraction:
    text: str
    method: str


def extract_text(kind: FileKind, data: bytes) -> Extraction:
    if kind.extractor == "pdf":
        return _pdf(data)
    if kind.extractor == "docx":
        return _docx(data)
    return _plain_text(data)


def _docx(data: bytes) -> Extraction:
    try:
        document = Document(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("This Word file could not be opened.") from exc

    parts: list[str] = [p.text for p in document.paragraphs if p.text.strip()]

    for index, table in enumerate(document.tables, start=1):
        parts.append(f"Table {index}:\n" + _table_to_text(table.rows))

    text = "\n\n".join(parts).strip()
    if not text:
        raise ExtractionError("No text was found in this Word file.")
    return Extraction(text=text, method="python-docx")


def _table_to_text(rows) -> str:
    lines = []
    for row in rows:
        cells = [cell.text.strip() for cell in row.cells]
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def _pdf(data: bytes) -> Extraction:
    try:
        pdf = pdfplumber.open(io.BytesIO(data))
    except Exception as exc:
        raise ExtractionError("This PDF could not be opened. It may be damaged.") from exc

    parts: list[str] = []
    with pdf:
        if len(pdf.pages) == 0:
            raise ExtractionError("This PDF has no pages.")

        for page_number, page in enumerate(pdf.pages, start=1):
            page_text = (page.extract_text() or "").strip()
            if page_text:
                parts.append(f"Page {page_number}:\n{page_text}")

            for index, table in enumerate(page.extract_tables(), start=1):
                rows = [[(cell or "").strip() for cell in row] for row in table if row]
                if rows:
                    lines = [" | ".join(row) for row in rows]
                    parts.append(f"Page {page_number}, table {index}:\n" + "\n".join(lines))

    text = "\n\n".join(parts).strip()
    if not text:
        raise ExtractionError(
            "No text was found in this PDF. It may be a scanned image, which is not supported yet."
        )
    return Extraction(text=text, method="pdfplumber")


def _plain_text(data: bytes) -> Extraction:
    try:
        text = data.decode("utf-8-sig").strip()
    except UnicodeDecodeError as exc:
        raise ExtractionError("This file is not valid UTF-8 text.") from exc
    if not text:
        raise ExtractionError("This file is empty.")
    return Extraction(text=text, method="utf-8")