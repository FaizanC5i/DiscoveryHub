# tests/test_upload_chunks.py
"""
Uploading a document must produce source -> content -> chunks in one request.
Uses an in-memory blob store and a fake extractor, so no Azure calls are made.
Run from backend/: python -m pytest -q tests/test_upload_chunks.py
"""

import pytest

from app.db.models import ContextChunk, ContextContent, ContextSource
from app.db.session import get_session_factory
from app.main import app
from app.services import chunking_service, context_chunk_service, context_service
from app.services.extraction.extractors import Extraction, ExtractionError
from app.services.storage.blob_storage import InMemoryBlobStorage, get_blob_storage


@pytest.fixture
def storage():
    fake = InMemoryBlobStorage()
    app.dependency_overrides[get_blob_storage] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_blob_storage, None)


@pytest.fixture(autouse=True)
def fake_extract(monkeypatch):
    def _extract(kind, data):
        if b"UNREADABLE" in data:
            raise ExtractionError("No readable text was found in this file.")
        return Extraction(text=data.decode("utf-8", errors="ignore"), method="test")

    monkeypatch.setattr(context_service, "extract_text", _extract)


def _project(client) -> int:
    response = client.post("/api/projects", json={"name": "Discovery"})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _upload(client, project_id: int, name: str, data: bytes):
    return client.post(
        f"/api/projects/{project_id}/sources",
        files={"file": (name, data, "text/plain")},
    )


def _rows_for_source(source_id: int):
    """Read what is actually stored: the source, its content and its chunks."""
    with get_session_factory()() as db:
        source = db.get(ContextSource, source_id)
        content = db.query(ContextContent).filter(ContextContent.context_source_id == source_id).one_or_none()
        chunks = []
        if content is not None:
            chunks = (
                db.query(ContextChunk)
                .filter(ContextChunk.context_content_id == content.id)
                .order_by(ContextChunk.chunk_number)
                .all()
            )
        return (
            source.processing_status,
            source.failure_reason,
            content.content_text if content else None,
            [(c.chunk_number, c.start_char, c.end_char, c.chunk_text) for c in chunks],
        )


def _long_text() -> str:
    return " ".join(f"The team reviews item {n} in the discovery workshop." for n in range(1, 60))


def test_upload_saves_source_content_and_chunks_in_one_request(make_user, storage):
    alice = make_user("upchunk-ok")
    project_id = _project(alice.client)
    text = _long_text()

    response = _upload(alice.client, project_id, "workshop.txt", text.encode())

    assert response.status_code == 201
    body = response.json()
    assert body["processing_status"] == "ready"

    status, reason, content_text, chunks = _rows_for_source(body["id"])
    assert status == "ready" and reason is None
    assert content_text == text
    assert len(chunks) > 1
    assert [number for number, *_ in chunks] == list(range(1, len(chunks) + 1))
    for _, start, end, chunk_text in chunks:
        assert text[start:end] == chunk_text


def test_chunks_are_readable_through_the_api_after_upload(make_user, storage):
    alice = make_user("upchunk-api")
    project_id = _project(alice.client)
    source = _upload(alice.client, project_id, "notes.txt", _long_text().encode()).json()
    with get_session_factory()() as db:
        content_id = db.query(ContextContent).filter(ContextContent.context_source_id == source["id"]).one().id

    response = alice.client.get(f"/api/context-content/{content_id}/chunks")

    assert response.status_code == 200
    assert len(response.json()) > 1


def test_failed_extraction_creates_no_chunks(make_user, storage):
    alice = make_user("upchunk-unreadable")
    project_id = _project(alice.client)

    response = _upload(alice.client, project_id, "scan.txt", b"UNREADABLE")

    assert response.status_code == 201
    status, _, content_text, chunks = _rows_for_source(response.json()["id"])
    assert status == "failed"
    assert content_text is None
    assert chunks == []


def test_chunking_error_keeps_the_upload_and_marks_the_source_failed(make_user, storage, monkeypatch):
    alice = make_user("upchunk-fail")
    project_id = _project(alice.client)

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated chunker failure")

    monkeypatch.setattr(context_chunk_service, "chunk_text", _explode)

    response = _upload(alice.client, project_id, "plan.txt", _long_text().encode())

    assert response.status_code == 201
    body = response.json()
    assert body["processing_status"] == "failed"
    assert body["failure_reason"] == context_chunk_service.FAILURE_REASON
    status, _, content_text, chunks = _rows_for_source(body["id"])
    assert status == "failed"
    assert content_text is not None  # the extracted text is kept for Retry
    assert chunks == []


def test_retry_creates_chunks_after_a_failed_chunking_run(make_user, storage, monkeypatch):
    alice = make_user("upchunk-retry")
    project_id = _project(alice.client)
    real_chunk_text = chunking_service.chunk_text

    def _explode(*args, **kwargs):
        raise RuntimeError("simulated chunker failure")

    monkeypatch.setattr(context_chunk_service, "chunk_text", _explode)
    source = _upload(alice.client, project_id, "plan.txt", _long_text().encode()).json()

    monkeypatch.setattr(context_chunk_service, "chunk_text", real_chunk_text)
    response = alice.client.post(f"/api/projects/{project_id}/sources/{source['id']}/reprocess")

    assert response.status_code == 200
    assert response.json()["processing_status"] == "ready"
    _, _, _, chunks = _rows_for_source(source["id"])
    assert len(chunks) > 1


def test_retry_refuses_to_change_text_that_already_has_chunks(make_user, storage, monkeypatch):
    alice = make_user("upchunk-changed")
    project_id = _project(alice.client)
    source = _upload(alice.client, project_id, "plan.txt", _long_text().encode()).json()
    _, _, original_text, before = _rows_for_source(source["id"])

    def _different(kind, data):
        return Extraction(text="A completely different text.", method="test")

    monkeypatch.setattr(context_service, "extract_text", _different)
    response = alice.client.post(f"/api/projects/{project_id}/sources/{source['id']}/reprocess")

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "CONTENT_HAS_CHUNKS"
    _, _, text_after, after = _rows_for_source(source["id"])
    assert text_after == original_text
    assert after == before


def test_retry_with_the_same_text_reuses_existing_chunks(make_user, storage):
    alice = make_user("upchunk-same")
    project_id = _project(alice.client)
    source = _upload(alice.client, project_id, "plan.txt", _long_text().encode()).json()
    _, _, _, before = _rows_for_source(source["id"])

    response = alice.client.post(f"/api/projects/{project_id}/sources/{source['id']}/reprocess")

    assert response.status_code == 200
    _, _, _, after = _rows_for_source(source["id"])
    assert after == before
