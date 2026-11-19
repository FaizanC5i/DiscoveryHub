"""
Turns an uploaded meeting transcript into plain text.

Analogy: the reading room. Each file goes to the reader that understands its format. A file
that cannot be read as text is refused with a reason, never guessed at.
"""

import io
import re
from pathlib import Path

import pdfplumber
from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph

MAX_FILE_BYTES = 25 * 1024 * 1024


class TranscriptError(Exception):
    """The file cannot be used as a transcript. The message is safe to show the user."""


def read_transcript(name: str, raw: bytes) -> str:
    if not raw:
        raise TranscriptError(f"{name} is empty.")
    if len(raw) > MAX_FILE_BYTES:
        raise TranscriptError(f"{name} is larger than 25 MB.")

    extension = Path(name).suffix.lower()
    if extension == ".docx":
        text = _docx_text(name, raw)
    elif extension == ".pdf":
        text = _pdf_text(name, raw)
    elif extension in (".html", ".htm"):
        text = _strip_html(_decode(name, raw))
    elif extension == ".rtf":
        text = _strip_rtf(_decode(name, raw))
    elif extension == ".doc":
        raise TranscriptError(f"{name}: older .doc files are not supported. Save it as .docx and upload again.")
    else:
        # TXT, MD, VTT, SRT, JSON, CSV, LOG and other text-based files are read as text.
        text = _decode(name, raw)

    if not text.strip():
        raise TranscriptError(f"{name} has no readable text.")
    return text.strip()


def _decode(name: str, raw: bytes) -> str:
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16", errors="replace")
    if b"\x00" in raw[:4096]:
        raise TranscriptError(f"{name} looks like a binary file and cannot be read as text.")
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        return raw.decode("cp1252", errors="replace")


def _docx_text(name: str, raw: bytes) -> str:
    try:
        document = Document(io.BytesIO(raw))
    except Exception:
        raise TranscriptError(f"{name} is not a readable Word document.") from None

    lines: list[str] = []
    for child in document.element.body.iterchildren():
        if child.tag.endswith("}p"):
            lines.append(Paragraph(child, document).text)
        elif child.tag.endswith("}tbl"):
            for row in Table(child, document).rows:
                lines.append(" | ".join(cell.text.strip() for cell in row.cells))
    return "\n".join(lines)


def _pdf_text(name: str, raw: bytes) -> str:
    try:
        with pdfplumber.open(io.BytesIO(raw)) as pdf:
            text = "\n\n".join((page.extract_text() or "") for page in pdf.pages)
    except Exception:
        raise TranscriptError(f"{name} could not be read. It may be password protected or damaged.") from None
    if not text.strip():
        raise TranscriptError(f"{name} has no text. It may be a scanned image.")
    return text


def _strip_html(text: str) -> str:
    text = re.sub(r"(?is)<(script|style).*?>.*?</\1>", " ", text)
    text = re.sub(r"(?i)<br\s*/?>|</p>|</div>|</li>|</tr>", "\n", text)
    text = re.sub(r"(?s)<[^>]+>", " ", text)
    for old, new in {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"', "&#39;": "'"}.items():
        text = text.replace(old, new)
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def _strip_rtf(text: str) -> str:
    text = re.sub(r"\\par[d]?", "\n", text)
    text = re.sub(r"\\'[0-9a-fA-F]{2}", "", text)
    text = re.sub(r"\\[a-zA-Z]+-?\d* ?", "", text)
    return re.sub(r"[{}]", "", text).strip()
