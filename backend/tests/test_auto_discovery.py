"""
Unit tests for auto-starting User Discovery after chunk mapping completes.
The run covers only the chunks this mapping job just mapped. No database or network: all
collaborators are monkeypatched.

Run from backend/: python -m pytest -q tests/test_auto_discovery.py
"""

from unittest.mock import MagicMock, patch

from app.services import chunk_mapping_service


def _session_factory(new_mapped_ids: list[int]):
    """A session factory whose db.scalars(...) returns the given chunk ids."""
    db = MagicMock()
    db.scalars.return_value = iter(new_mapped_ids)
    context = MagicMock()
    context.__enter__ = MagicMock(return_value=db)
    context.__exit__ = MagicMock(return_value=False)
    factory = MagicMock(return_value=context)
    return factory


class TestStartUserDiscoveryIfReady:

    def test_starts_run_on_newly_mapped_chunks_only(self):
        factory = _session_factory([101, 102])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", return_value=factory),
            patch.object(chunk_mapping_service, "pending_mapping_count", return_value=0),
            patch.object(chunk_mapping_service.answer_pipeline, "is_running", return_value=False),
            patch.object(chunk_mapping_service.threading, "Thread") as mock_thread,
        ):
            chunk_mapping_service._start_user_discovery_if_ready(42, [101, 102, 103])

        mock_thread.assert_called_once()
        kwargs = mock_thread.call_args.kwargs
        assert kwargs["target"] is chunk_mapping_service.answer_pipeline.run_in_background
        assert kwargs["args"] == (42, None, {101, 102})
        mock_thread.return_value.start.assert_called_once()

    def test_does_not_start_when_chunks_still_pending(self):
        factory = _session_factory([101])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", return_value=factory),
            patch.object(chunk_mapping_service, "pending_mapping_count", return_value=3),
            patch.object(chunk_mapping_service.threading, "Thread") as mock_thread,
        ):
            chunk_mapping_service._start_user_discovery_if_ready(42, [101])

        mock_thread.assert_not_called()

    def test_does_not_start_when_no_chunk_was_newly_mapped(self):
        factory = _session_factory([])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", return_value=factory),
            patch.object(chunk_mapping_service, "pending_mapping_count", return_value=0),
            patch.object(chunk_mapping_service.threading, "Thread") as mock_thread,
        ):
            chunk_mapping_service._start_user_discovery_if_ready(42, [101])

        mock_thread.assert_not_called()

    def test_does_not_start_when_already_running(self):
        factory = _session_factory([101])
        with (
            patch.object(chunk_mapping_service, "get_session_factory", return_value=factory),
            patch.object(chunk_mapping_service, "pending_mapping_count", return_value=0),
            patch.object(chunk_mapping_service.answer_pipeline, "is_running", return_value=True),
            patch.object(chunk_mapping_service.threading, "Thread") as mock_thread,
        ):
            chunk_mapping_service._start_user_discovery_if_ready(42, [101])

        mock_thread.assert_not_called()

    def test_exception_is_swallowed_and_does_not_propagate(self):
        with patch.object(chunk_mapping_service, "get_session_factory", side_effect=RuntimeError("db down")):
            chunk_mapping_service._start_user_discovery_if_ready(42, [101])
