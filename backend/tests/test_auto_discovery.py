"""
Unit tests for auto-starting User Discovery after chunk mapping completes.
No database or network: all collaborators are monkeypatched.

Run from backend/: python -m pytest -q tests/test_auto_discovery.py
"""

from unittest.mock import MagicMock, patch

from app.services import chunk_mapping_service


def _mock_session_factory(pending: int, mapping_rows: list):
    """Return a session-factory mock whose context-manager yields a db session."""
    mock_db = MagicMock()
    factory = MagicMock()
    cm = MagicMock()
    cm.__enter__ = MagicMock(return_value=mock_db)
    cm.__exit__ = MagicMock(return_value=False)
    factory.return_value = cm
    return factory, mock_db


class TestStartUserDiscoveryIfReady:

    def test_calls_run_in_background_when_all_conditions_met(self):
        factory, mock_db = _mock_session_factory(0, [{"x": 1}])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", return_value=factory),
            patch.object(chunk_mapping_service, "pending_mapping_count", return_value=0),
            patch.object(chunk_mapping_service, "project_mapping_rows", return_value=[{"x": 1}]),
            patch.object(chunk_mapping_service.answer_pipeline, "is_running", return_value=False),
            patch.object(chunk_mapping_service.answer_pipeline, "run_in_background") as mock_run,
        ):
            chunk_mapping_service._start_user_discovery_if_ready(42)

        mock_run.assert_called_once_with(42, None)

    def test_does_not_start_when_chunks_still_pending(self):
        factory, mock_db = _mock_session_factory(3, [])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", return_value=factory),
            patch.object(chunk_mapping_service, "pending_mapping_count", return_value=3),
            patch.object(chunk_mapping_service.answer_pipeline, "run_in_background") as mock_run,
        ):
            chunk_mapping_service._start_user_discovery_if_ready(42)

        mock_run.assert_not_called()

    def test_does_not_start_when_no_mapping_rows(self):
        factory, mock_db = _mock_session_factory(0, [])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", return_value=factory),
            patch.object(chunk_mapping_service, "pending_mapping_count", return_value=0),
            patch.object(chunk_mapping_service, "project_mapping_rows", return_value=[]),
            patch.object(chunk_mapping_service.answer_pipeline, "run_in_background") as mock_run,
        ):
            chunk_mapping_service._start_user_discovery_if_ready(42)

        mock_run.assert_not_called()

    def test_does_not_start_when_already_running(self):
        factory, mock_db = _mock_session_factory(0, [{"x": 1}])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", return_value=factory),
            patch.object(chunk_mapping_service, "pending_mapping_count", return_value=0),
            patch.object(chunk_mapping_service, "project_mapping_rows", return_value=[{"x": 1}]),
            patch.object(chunk_mapping_service.answer_pipeline, "is_running", return_value=True),
            patch.object(chunk_mapping_service.answer_pipeline, "run_in_background") as mock_run,
        ):
            chunk_mapping_service._start_user_discovery_if_ready(42)

        mock_run.assert_not_called()

    def test_exception_is_swallowed_and_does_not_propagate(self):
        factory, mock_db = _mock_session_factory(0, [])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", side_effect=RuntimeError("db down")),
        ):
            # Must not raise
            chunk_mapping_service._start_user_discovery_if_ready(42)
