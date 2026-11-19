# tests/test_context_sources.py
"""
Tests for /api/projects/{id}/sources. Uses an in-memory blob store and a fake OCR
step, so no Azure calls are made. Run from backend/: python -m pytest -q tests/test_context_sources.py
"""

import pytest

from app.main import app
from app.services import context_service
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


def _upload(client, project_id: int, name: str, data: bytes, mime: str = "text/plain"):
    return client.post(f"/api/projects/{project_id}/sources", files={"file": (name, data, mime)})


def test_text_upload_is_stored_and_ready(make_user, storage):
    alice = make_user("src-ok")
    project_id = _project(alice.client)

    response = _upload(alice.client, project_id, "notes.txt", b"Hello discovery")

    assert response.status_code == 201
    body = response.json()
    assert body["processing_status"] == "ready"
    assert body["failure_reason"] is None
    assert len(storage.blobs) == 1
    listed = alice.client.get(f"/api/projects/{project_id}/sources").json()
    assert [item["id"] for item in listed] == [body["id"]]


def test_unsupported_extension_is_rejected_before_storage(make_user, storage):
    alice = make_user("src-type")
    project_id = _project(alice.client)

    response = _upload(alice.client, project_id, "tool.exe", b"MZ\x90\x00", "application/octet-stream")

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "UNSUPPORTED_FILE_TYPE"
    assert storage.blobs == {}


def test_content_that_does_not_match_extension_is_rejected(make_user, storage):
    alice = make_user("src-sig")
    project_id = _project(alice.client)

    response = _upload(alice.client, project_id, "report.pdf", b"not really a pdf", "application/pdf")

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_FILE_CONTENT"
    assert storage.blobs == {}


def test_recognition_failure_keeps_source_as_failed(make_user, storage):
    alice = make_user("src-ocr")
    project_id = _project(alice.client)

    response = _upload(alice.client, project_id, "scan.pdf", b"%PDF-1.4 UNREADABLE", "application/pdf")

    assert response.status_code == 201
    body = response.json()
    assert body["processing_status"] == "failed"
    assert "No readable text" in body["failure_reason"]
    assert len(storage.blobs) == 1  # kept so Retry can run again


def test_another_users_project_returns_404(make_user, storage):
    alice = make_user("src-owner")
    bob = make_user("src-intruder")
    project_id = _project(alice.client)

    response = _upload(bob.client, project_id, "notes.txt", b"private")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"
    assert storage.blobs == {}


def test_delete_hides_source_and_removes_blob(make_user, storage):
    alice = make_user("src-delete")
    project_id = _project(alice.client)
    source_id = _upload(alice.client, project_id, "notes.txt", b"temporary").json()["id"]

    response = alice.client.delete(f"/api/projects/{project_id}/sources/{source_id}")

    assert response.status_code == 204
    assert alice.client.get(f"/api/projects/{project_id}/sources").json() == []
    assert storage.blobs == {}