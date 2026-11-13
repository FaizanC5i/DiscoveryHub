# tests/test_project_delete.py
"""
Deleting a project removes everything under it: sources, extracted text, chunks and
original files. Uses an in-memory blob store and a fake extractor, so no Azure calls are made.
Run from backend/: python -m pytest -q tests/test_project_delete.py
"""

import pytest

from app.db.models import ContextChunk, ContextContent, ContextSource, Project
from app.db.session import get_session_factory
from app.main import app
from app.services import context_service
from app.services.extraction.extractors import Extraction
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
        return Extraction(text=data.decode("utf-8", errors="ignore"), method="test")

    monkeypatch.setattr(context_service, "extract_text", _extract)


def _project(client, name: str = "Discovery") -> int:
    response = client.post("/api/projects", json={"name": name})
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _upload_documents(client, project_id: int, count: int = 2) -> None:
    text = " ".join(f"The team reviews item {n} in the workshop." for n in range(1, 40))
    for index in range(count):
        response = client.post(
            f"/api/projects/{project_id}/sources",
            files={"file": (f"doc{index}.txt", text.encode(), "text/plain")},
        )
        assert response.status_code == 201, response.text


def _counts(project_id: int) -> dict[str, int]:
    """How many rows of each kind still exist for this project."""
    with get_session_factory()() as db:
        source_ids = [s.id for s in db.query(ContextSource).filter(ContextSource.project_id == project_id)]
        content_ids = [
            c.id for c in db.query(ContextContent).filter(ContextContent.context_source_id.in_(source_ids))
        ] if source_ids else []
        return {
            "projects": db.query(Project).filter(Project.id == project_id).count(),
            "sources": len(source_ids),
            "content": len(content_ids),
            "chunks": db.query(ContextChunk).filter(ContextChunk.context_content_id.in_(content_ids)).count()
            if content_ids
            else 0,
        }


def test_delete_removes_sources_text_chunks_and_original_files(make_user, storage):
    alice = make_user("delproj-all")
    project_id = _project(alice.client)
    _upload_documents(alice.client, project_id)
    before = _counts(project_id)
    assert before["sources"] == 2 and before["content"] == 2 and before["chunks"] > 2
    assert len(storage.blobs) == 2

    response = alice.client.delete(f"/api/projects/{project_id}")

    assert response.status_code == 204
    assert _counts(project_id) == {"projects": 0, "sources": 0, "content": 0, "chunks": 0}
    assert storage.blobs == {}


def test_deleted_project_is_no_longer_visible(make_user, storage):
    alice = make_user("delproj-gone")
    project_id = _project(alice.client)

    alice.client.delete(f"/api/projects/{project_id}")

    assert alice.client.get(f"/api/projects/{project_id}").status_code == 404
    assert alice.client.delete(f"/api/projects/{project_id}").status_code == 404


def test_another_users_project_cannot_be_deleted(make_user, storage):
    alice = make_user("delproj-owner")
    bob = make_user("delproj-intruder")
    project_id = _project(alice.client)
    _upload_documents(alice.client, project_id, count=1)

    response = bob.client.delete(f"/api/projects/{project_id}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"
    assert _counts(project_id)["sources"] == 1
    assert len(storage.blobs) == 1


def test_missing_project_returns_404(make_user, storage):
    alice = make_user("delproj-missing")

    response = alice.client.delete("/api/projects/999999999")

    assert response.status_code == 404


def test_deleting_one_project_leaves_the_others_untouched(make_user, storage):
    alice = make_user("delproj-two")
    doomed = _project(alice.client, "Doomed")
    kept = _project(alice.client, "Kept")
    _upload_documents(alice.client, doomed)
    _upload_documents(alice.client, kept)
    kept_before = _counts(kept)

    alice.client.delete(f"/api/projects/{doomed}")

    assert _counts(kept) == kept_before
    assert alice.client.get(f"/api/projects/{kept}").status_code == 200


def test_a_failed_file_delete_does_not_undo_the_project_delete(make_user, storage, monkeypatch):
    alice = make_user("delproj-blobfail")
    project_id = _project(alice.client)
    _upload_documents(alice.client, project_id, count=1)

    def _broken(key):
        raise RuntimeError("storage unavailable")

    monkeypatch.setattr(storage, "delete", _broken)

    response = alice.client.delete(f"/api/projects/{project_id}")

    assert response.status_code == 204
    assert _counts(project_id)["projects"] == 0


def test_delete_requires_sign_in(make_user, storage):
    alice = make_user("delproj-anon")
    project_id = _project(alice.client)

    from fastapi.testclient import TestClient

    anonymous = TestClient(app)
    assert anonymous.delete(f"/api/projects/{project_id}").status_code == 401
    assert _counts(project_id)["projects"] == 1
