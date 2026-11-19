# tests/test_context_chunks.py
"""
Tests for /api/context-content/{id}/chunks. These run against the real database
named in backend/.env. Content rows are written directly, so no blob storage or
OCR is involved. Users are deleted at the end, which cascades to their rows.
Run from backend/: python -m pytest -q tests/test_context_chunks.py
"""

import uuid

import pytest

from app.core.time import utc_now
from app.db.models import ContextChunk, ContextContent, ContextSource
from app.db.session import get_session_factory
from app.services import chunking_service, context_chunk_service


def _project(client) -> int:
    response = client.post("/api/projects", json={"name": "Discovery"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _content(user_id: int, project_id: int, text: str, deleted: bool = False) -> int:
    """Write a source and its extracted text, the way a successful upload would."""
    with get_session_factory()() as db:
        source = ContextSource(
            project_id=project_id,
            created_by=user_id,
            title="Requirements",
            original_filename="requirements.txt",
            blob_path=f"tests/{uuid.uuid4().hex}.txt",
            mime_type="text/plain",
            file_size_bytes=len(text.encode("utf-8")),
            processing_status="ready",
            deleted_at=utc_now() if deleted else None,
        )
        source.content = ContextContent(content_text=text, extraction_method="test")
        db.add(source)
        db.commit()
        return source.content.id


def _source_status(content_id: int) -> tuple[str, str | None]:
    with get_session_factory()() as db:
        content = db.get(ContextContent, content_id)
        source = db.get(ContextSource, content.context_source_id)
        return source.processing_status, source.failure_reason


def _long_text(count: int = 40) -> str:
    return " ".join(f"The system records review step {n} for the project." for n in range(1, count + 1))


def test_first_call_creates_chunks_and_second_call_creates_none(make_user):
    alice = make_user("chunk-create")
    project_id = _project(alice.client)
    content_id = _content(alice.id, project_id, _long_text())

    first = alice.client.post(f"/api/context-content/{content_id}/chunks")
    second = alice.client.post(f"/api/context-content/{content_id}/chunks")

    assert first.status_code == 201
    assert second.status_code == 200
    created = first.json()
    assert len(created) > 1
    assert [chunk["id"] for chunk in second.json()] == [chunk["id"] for chunk in created]
    assert [chunk["chunk_number"] for chunk in created] == list(range(1, len(created) + 1))


def test_chunks_are_listed_in_order_with_offsets_that_match_the_text(make_user):
    alice = make_user("chunk-list")
    project_id = _project(alice.client)
    text = "Page 1:\n" + _long_text(30) + "\nPage 2:\n" + _long_text(10)
    content_id = _content(alice.id, project_id, text)
    alice.client.post(f"/api/context-content/{content_id}/chunks")

    response = alice.client.get(f"/api/context-content/{content_id}/chunks")

    assert response.status_code == 200
    chunks = response.json()
    assert [chunk["chunk_number"] for chunk in chunks] == list(range(1, len(chunks) + 1))
    for chunk in chunks:
        assert text[chunk["start_char"] : chunk["end_char"]] == chunk["chunk_text"]
        assert chunk["char_count"] == chunk["end_char"] - chunk["start_char"]
    assert chunks[0]["page_number"] == 1
    assert chunks[-1]["page_number"] == 2


def test_chunking_marks_the_source_ready_and_chunks_are_saved_once(make_user):
    alice = make_user("chunk-status")
    project_id = _project(alice.client)
    content_id = _content(alice.id, project_id, _long_text())

    alice.client.post(f"/api/context-content/{content_id}/chunks")

    assert _source_status(content_id) == ("ready", None)
    with get_session_factory()() as db:
        stored = db.query(ContextChunk).filter(ContextChunk.context_content_id == content_id).count()
    assert stored == len(alice.client.get(f"/api/context-content/{content_id}/chunks").json())


def test_second_user_gets_404_for_create_and_list(make_user):
    alice = make_user("chunk-owner")
    bob = make_user("chunk-intruder")
    project_id = _project(alice.client)
    content_id = _content(alice.id, project_id, _long_text())

    create = bob.client.post(f"/api/context-content/{content_id}/chunks")
    listing = bob.client.get(f"/api/context-content/{content_id}/chunks")

    assert create.status_code == 404
    assert listing.status_code == 404
    assert create.json()["detail"]["code"] == "CONTENT_NOT_FOUND"
    assert listing.json()["detail"]["code"] == "CONTENT_NOT_FOUND"


def test_missing_content_returns_the_same_404(make_user):
    alice = make_user("chunk-missing")

    response = alice.client.post("/api/context-content/999999999/chunks")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "CONTENT_NOT_FOUND"


def test_deleted_source_cannot_be_chunked(make_user):
    alice = make_user("chunk-deleted")
    project_id = _project(alice.client)
    content_id = _content(alice.id, project_id, _long_text(), deleted=True)

    response = alice.client.post(f"/api/context-content/{content_id}/chunks")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "SOURCE_DELETED"


def test_failure_marks_the_source_failed_and_saves_nothing(make_user, monkeypatch):
    alice = make_user("chunk-fail")
    project_id = _project(alice.client)
    content_id = _content(alice.id, project_id, _long_text())

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated chunker failure")

    monkeypatch.setattr(context_chunk_service, "chunk_text", _explode)

    response = alice.client.post(f"/api/context-content/{content_id}/chunks")

    assert response.status_code == 500
    assert response.json()["detail"]["code"] == "CHUNKING_FAILED"
    assert _source_status(content_id) == ("failed", context_chunk_service.FAILURE_REASON)
    assert alice.client.get(f"/api/context-content/{content_id}/chunks").json() == []


def test_chunk_settings_come_from_configuration(make_user, monkeypatch):
    alice = make_user("chunk-config")
    project_id = _project(alice.client)
    content_id = _content(alice.id, project_id, _long_text(20))
    seen = {}

    real_chunk_text = chunking_service.chunk_text

    def _spy(text, max_chars, overlap_chars):
        seen["max"], seen["overlap"] = max_chars, overlap_chars
        return real_chunk_text(text, max_chars=max_chars, overlap_chars=overlap_chars)

    class _Settings:
        chunk_max_chars = 321
        chunk_overlap_chars = 45

    monkeypatch.setattr(context_chunk_service, "chunk_text", _spy)
    monkeypatch.setattr(context_chunk_service, "get_settings", lambda: _Settings())

    alice.client.post(f"/api/context-content/{content_id}/chunks")

    assert seen == {"max": 321, "overlap": 45}


def test_chunk_endpoints_require_sign_in(make_user):
    alice = make_user("chunk-anon")
    project_id = _project(alice.client)
    content_id = _content(alice.id, project_id, _long_text())

    from fastapi.testclient import TestClient

    from app.main import app

    anonymous = TestClient(app)
    assert anonymous.get(f"/api/context-content/{content_id}/chunks").status_code == 401
    assert anonymous.post(f"/api/context-content/{content_id}/chunks").status_code == 401
