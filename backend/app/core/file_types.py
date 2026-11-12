"""
Which files we accept, and a check that the content matches the extension.

The extension is what the user typed. The first bytes are what the file really is.
Checking both stops a renamed program (for example malware.exe saved as report.pdf)
from being accepted.
"""

import io
import zipfile
from dataclasses import dataclass
from pathlib import PurePosixPath

from app.core.errors import api_error


@dataclass(frozen=True)
class FileKind:
    extension: str
    mime_type: str
    extractor: str  # "ocr", "docx", or "text"


ALLOWED_KINDS: dict[str, FileKind] = {
    ".pdf": FileKind(".pdf", "application/pdf", "pdf"),
    ".docx": FileKind(
        ".docx",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "docx",
    ),
    ".txt": FileKind(".txt", "text/plain", "text"),
    ".md": FileKind(".md", "text/markdown", "text"),
}

PDF_SIGNATURE = b"%PDF-"
ZIP_SIGNATURE = b"PK\x03\x04"


def basename(filename: str) -> str:
    """The file name without any folder part, whichever slash the browser sent."""
    return PurePosixPath(filename.replace("\\", "/")).name


def resolve_kind(filename: str) -> FileKind:
    suffix = PurePosixPath(basename(filename)).suffix.lower()
    kind = ALLOWED_KINDS.get(suffix)
    if kind is None:
        raise api_error(
            422,
            "UNSUPPORTED_FILE_TYPE",
            "Use a PDF, DOCX, TXT, Markdown, PNG, or JPG file.",
        )
    return kind


def check_content(kind: FileKind, data: bytes) -> None:
    """Raise 422 when the bytes do not look like the type the extension claims."""
    if kind.extension == ".pdf":
        valid = data.startswith(PDF_SIGNATURE)
    elif kind.extension == ".docx":
        valid = _is_docx(data)
    else:
        valid = b"\x00" not in data and _is_utf8(data)

    if not valid:
        label = kind.extension.lstrip(".").upper()
        raise api_error(
            422,
            "INVALID_FILE_CONTENT",
            f"This file does not look like a valid {label} file.",
        )


def _is_docx(data: bytes) -> bool:
    if not data.startswith(ZIP_SIGNATURE):
        return False
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            return "word/document.xml" in archive.namelist()
    except zipfile.BadZipFile:
        return False


def _is_utf8(data: bytes) -> bool:
    try:
        data.decode("utf-8-sig")
        return True
    except UnicodeDecodeError:
        return False