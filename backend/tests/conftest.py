# tests/conftest.py
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