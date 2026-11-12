"""
Tests for the /api/projects endpoints.

These run against the real database named in backend/.env. Each test creates its
own users with unique emails and deletes them at the end. Their projects go with
them through the database's ON DELETE CASCADE, so nothing is left behind.

Run from backend/:  python -m pytest -q
"""

import time
import uuid
from collections.abc import Callable, Iterator
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient

from app.core.cookies import ACCESS_COOKIE
from app.db.models import User
from app.db.session import get_session_factory
from app.main import app
from app.services import auth_service

PASSWORD = "Passw0rd1"


@dataclass
class SignedInUser:
    id: int
    client: TestClient


@pytest.fixture
def make_user() -> Iterator[Callable[[str], SignedInUser]]:
    """
    Creates a signed-in user and returns an HTTP client that carries their access cookie.

    Analogy: issuing a visitor badge. The badge is printed for a real account, and
    the client holds it the way a browser would. All badges are collected at the
    end of the test.
    """
    created_ids: list[int] = []
    sessions = get_session_factory()

    def _make(label: str) -> SignedInUser:
        email = f"test-{label}-{uuid.uuid4().hex[:10]}@example.com"
        with sessions() as db:
            user = auth_service.sign_up(db, f"Test {label}", email, PASSWORD)
            session = auth_service.issue_session(db, user)
            user_id = user.id
        created_ids.append(user_id)

        client = TestClient(app)
        client.cookies.set(ACCESS_COOKIE, session.access_token)
        return SignedInUser(id=user_id, client=client)

    yield _make

    with sessions() as db:
        for user_id in created_ids:
            user = db.get(User, user_id)
            if user is not None:
                db.delete(user)
        db.commit()


def _create(client: TestClient, **overrides) -> dict:
    body = {"name": "Atlas Service Hub", "description": "Service desk discovery"}
    body.update(overrides)
    response = client.post("/api/projects", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def test_create_project_returns_201_with_owner_name(make_user):
    alice = make_user("create")

    project = _create(
        alice.client,
        name="  Atlas Service Hub  ",
        description="  Service desk discovery  ",
        start_date="2026-11-01",
        end_date="2026-12-31",
    )

    assert project["name"] == "Atlas Service Hub"
    assert project["description"] == "Service desk discovery"
    assert project["owner_id"] == alice.id
    assert project["owner_name"] == "Test create"
    assert project["start_date"] == "2026-11-01"
    assert project["end_date"] == "2026-12-31"
    # Timestamps carry a UTC offset, so the browser can convert them to local time.
    assert project["created_at"].endswith("+00:00")


def test_empty_description_is_stored_as_null(make_user):
    alice = make_user("nulldesc")

    project = _create(alice.client, description="   ")

    assert project["description"] is None


def test_list_returns_only_the_owners_projects(make_user):
    alice = make_user("list-a")
    bob = make_user("list-b")
    alice_project = _create(alice.client, name="Alice project")
    _create(bob.client, name="Bob project")

    response = alice.client.get("/api/projects", params={"limit": 5})

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert alice_project["id"] in ids
    assert all(item["owner_id"] == alice.id for item in response.json())
    assert "Bob project" not in [item["name"] for item in response.json()]


def test_list_is_newest_first_and_respects_limit(make_user):
    alice = make_user("order")
    first = _create(alice.client, name="First")
    second = _create(alice.client, name="Second")
    third = _create(alice.client, name="Third")

    response = alice.client.get("/api/projects", params={"limit": 2})

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert ids == [third["id"], second["id"]]
    assert first["id"] not in ids


def test_get_another_users_project_returns_404(make_user):
    alice = make_user("owner")
    bob = make_user("intruder")
    alice_project = _create(alice.client)

    response = bob.client.get(f"/api/projects/{alice_project['id']}")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_get_missing_project_returns_the_same_404(make_user):
    alice = make_user("missing")

    response = alice.client.get("/api/projects/999999999")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PROJECT_NOT_FOUND"


def test_invalid_date_range_returns_422(make_user):
    alice = make_user("badrange")

    response = alice.client.post(
        "/api/projects",
        json={"name": "Backwards", "start_date": "2026-12-31", "end_date": "2026-01-01"},
    )

    assert response.status_code == 422


def test_blank_name_returns_422(make_user):
    alice = make_user("blankname")

    response = alice.client.post("/api/projects", json={"name": "   "})

    assert response.status_code == 422


def test_update_changes_fields_and_updated_at(make_user):
    alice = make_user("update")
    project = _create(alice.client)
    time.sleep(0.05)  # make sure the new timestamp is clearly later

    response = alice.client.patch(
        f"/api/projects/{project['id']}",
        json={"name": "Renamed hub", "description": None},
    )

    assert response.status_code == 200
    updated = response.json()
    assert updated["name"] == "Renamed hub"
    assert updated["description"] is None
    assert updated["updated_at"] > project["updated_at"]
    assert updated["created_at"] == project["created_at"]


def test_partial_update_is_checked_against_stored_start_date(make_user):
    alice = make_user("partial")
    project = _create(alice.client, start_date="2026-06-01")

    response = alice.client.patch(
        f"/api/projects/{project['id']}",
        json={"end_date": "2026-05-01"},
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "INVALID_DATE_RANGE"

    unchanged = alice.client.get(f"/api/projects/{project['id']}").json()
    assert unchanged["end_date"] is None


def test_update_another_users_project_returns_404(make_user):
    alice = make_user("upd-owner")
    bob = make_user("upd-intruder")
    project = _create(alice.client)

    response = bob.client.patch(f"/api/projects/{project['id']}", json={"name": "Hijacked"})

    assert response.status_code == 404


def test_project_routes_require_sign_in():
    client = TestClient(app)

    response = client.get("/api/projects")

    assert response.status_code == 401
    assert response.json()["detail"]["code"] == "UNAUTHENTICATED"
