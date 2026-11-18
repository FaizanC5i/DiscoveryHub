"""BRD run start: a run refused by the one-running-run index becomes a 409, not a server error."""

from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.services import brd_service


class _Session:
    def __init__(self):
        self.added, self.rolled_back = [], False

    def execute(self, *_):
        return None

    def add(self, row):
        self.added.append(row)

    def commit(self):
        raise IntegrityError("INSERT agent_runs", {}, Exception("ux_agent_runs_one_running_artifact"))

    def rollback(self):
        self.rolled_back = True


def test_second_run_at_the_same_moment_is_a_409(monkeypatch):
    monkeypatch.setattr(brd_service, "_ensure_no_running_run", lambda db, artifact_id: None)
    monkeypatch.setattr(brd_service, "_brd_agent_id", lambda db: 1)
    db = _Session()
    artifact = SimpleNamespace(id=4, project_id=504)

    with pytest.raises(HTTPException) as info:
        brd_service._new_run(db, artifact, None, brd_service.RUN_GENERATE, {"mode": "generate_all"})

    assert info.value.status_code == 409
    assert info.value.detail["code"] == "BRD_RUN_IN_PROGRESS"
    assert db.rolled_back


def test_refresh_does_nothing_when_turned_off(monkeypatch):
    monkeypatch.setattr(brd_service, "get_settings", lambda: SimpleNamespace(brd_auto_refresh=False))
    monkeypatch.setattr(brd_service, "get_session_factory", lambda: pytest.fail("must not open the database"))
    brd_service.refresh_brd(504)
