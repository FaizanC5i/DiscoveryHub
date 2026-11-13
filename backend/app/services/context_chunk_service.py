"""
Saves the chunks for one extracted text, exactly once.

Analogy: the librarian who cuts a document into numbered index cards and files them.
Once the cards are filed, nobody re-cuts them. If the document changes, a new copy
gets its own cards, so every reference made to the old cards still points at the
same words.

Chunking is all-or-nothing: the chunk rows are written in one transaction, so a
failure part way through leaves no partial set behind.

Two entry points use the same work:
- create_chunks_for_content: the HTTP endpoint. A failure becomes an error response.
- chunk_uploaded_content: called by the upload and retry flows. A failure is recorded
  on the source (status "failed") and the upload itself still succeeds.
"""

import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import api_error
from app.db.models import ContextChunk, ContextContent, ContextSource, Project
from app.services.chunking_service import chunk_text, page_number_at

log = logging.getLogger(__name__)

# Shown to the user. The real exception goes to the server log only, so database or
# library details never reach the browser through failure_reason.
FAILURE_REASON = "The text could not be split into chunks."


@dataclass(frozen=True)
class ChunkResult:
    chunks: list[ContextChunk]
    created: bool


class _ChunkingFailed(Exception):
    """Internal signal: chunking failed and the source has already been marked failed."""


def create_chunks_for_content(db: Session, content_id: int, owner_id: int) -> ChunkResult:
    """
    Split the content into chunks and save them. Calling it again returns the chunks
    that already exist, so a double click or a retry cannot create duplicates.
    """
    content, source = _load_owned_content(db, content_id, owner_id)
    if source.deleted_at is not None:
        raise api_error(409, "SOURCE_DELETED", "This document was deleted, so it cannot be chunked.")
    try:
        return _chunk_content(db, content, source)
    except _ChunkingFailed:
        raise api_error(500, "CHUNKING_FAILED", FAILURE_REASON) from None


def chunk_uploaded_content(db: Session, content: ContextContent, source: ContextSource) -> None:
    """
    Chunk a document right after it was uploaded or retried. Never raises for a
    chunking failure: the source is marked failed, so the upload still returns and the
    user can press Retry.
    """
    try:
        _chunk_content(db, content, source)
    except _ChunkingFailed:
        pass


def has_chunks(db: Session, content_id: int) -> bool:
    return db.scalar(select(ContextChunk.id).where(ContextChunk.context_content_id == content_id).limit(1)) is not None


def list_chunks(db: Session, owner_id: int, content_id: int) -> list[ContextChunk]:
    content, source = _load_owned_content(db, content_id, owner_id)
    if source.deleted_at is not None:
        raise api_error(404, "CONTENT_NOT_FOUND", "Document text not found.")
    return _list_chunks(db, content.id)


# --- helpers -----------------------------------------------------------------


def _chunk_content(db: Session, content: ContextContent, source: ContextSource) -> ChunkResult:
    content_id = content.id
    source_id = source.id

    existing = _list_chunks(db, content_id)
    if existing:
        return ChunkResult(chunks=existing, created=False)

    # Show "processing" while the work runs, so the document does not look finished
    # until the chunks are saved.
    source.processing_status = "processing"
    db.commit()

    settings = get_settings()
    try:
        spans = chunk_text(
            content.content_text,
            max_chars=settings.chunk_max_chars,
            overlap_chars=settings.chunk_overlap_chars,
        )
        db.add_all(
            ContextChunk(
                context_content_id=content_id,
                chunk_number=span.chunk_number,
                chunk_text=span.text,
                start_char=span.start_char,
                end_char=span.end_char,
                char_count=span.end_char - span.start_char,
                page_number=page_number_at(content.content_text, span.start_char),
            )
            for span in spans
        )
        source.processing_status = "ready"
        source.failure_reason = None
        db.commit()
    except IntegrityError:
        # Another request saved the chunks between our check and our insert. The unique
        # key stopped the duplicate, so return what is stored instead of reporting a failure.
        db.rollback()
        return ChunkResult(chunks=_list_chunks(db, content_id), created=False)
    except Exception:
        db.rollback()
        log.exception("Chunking failed for content %s", content_id)
        _mark_failed(db, source_id)
        raise _ChunkingFailed() from None

    return ChunkResult(chunks=_list_chunks(db, content_id), created=True)


def _load_owned_content(db: Session, content_id: int, owner_id: int) -> tuple[ContextContent, ContextSource]:
    """
    Load the content only if its project belongs to the caller. A missing row and
    someone else's row give the same 404, so ids cannot be probed.
    """
    row = db.execute(
        select(ContextContent, ContextSource)
        .join(ContextSource, ContextSource.id == ContextContent.context_source_id)
        .join(Project, Project.id == ContextSource.project_id)
        .where(ContextContent.id == content_id, Project.owner_id == owner_id)
    ).first()
    if row is None:
        raise api_error(404, "CONTENT_NOT_FOUND", "Document text not found.")
    return row[0], row[1]


def _list_chunks(db: Session, content_id: int) -> list[ContextChunk]:
    return list(
        db.scalars(
            select(ContextChunk)
            .where(ContextChunk.context_content_id == content_id)
            .order_by(ContextChunk.chunk_number)
        )
    )


def _mark_failed(db: Session, source_id: int) -> None:
    source = db.get(ContextSource, source_id)
    if source is None:
        return
    source.processing_status = "failed"
    source.failure_reason = FAILURE_REASON
    db.commit()
