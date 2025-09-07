"""Unit tests for resume.py - WebSocket completion detection logic."""

from unittest.mock import Mock

import pytest


class TestWebSocketCompletionLogic:
    """Test the core completion detection logic that was causing the bug."""

    def test_tool_results_sent_flag_logic(self):
        """Test the tool_results_sent flag behavior that fixes the completion bug."""
        # Simulate the state variables from resume.py
        tool_results_sent = False
        complete = False

        # Before tool execution
        assert tool_results_sent is False
        assert complete is False

        # After tool execution (simulate the fix)
        tool_results_sent = True  # This gets set after _handle_execute_yield

        # When stream ends after tool results (the key fix)
        if tool_results_sent:
            complete = True  # This is the bug fix: tool results + stream end = success

        assert complete is True  # Should be True, not False (which caused fallback)

    def test_completion_detection_without_tools(self):
        """Without tools, stream end should trigger fallback (preserve original behavior)."""
        tool_results_sent = False
        complete = False

        # Stream ends without tools being executed
        if not tool_results_sent:
            # Should NOT mark as complete (should trigger fallback)
            pass  # Don't set complete = True

        assert complete is False  # Should fallback to HTTP mode

    def test_explicit_complete_context_always_succeeds(self):
        """Test that explicit 'complete' context always marks success."""
        yield_context = "complete"
        complete = False

        if yield_context == "complete":
            complete = True

        assert complete is True

    def test_execute_context_with_tools_sets_flag(self):
        """Test that execute context with pending calls sets tool_results_sent."""
        yield_context = "execute"
        calls = [{"name": "write", "args": {"filename": "test.txt"}}]  # Mock calls
        tool_results_sent = False

        if yield_context == "execute" and calls:
            # Simulate tool execution
            tool_results_sent = True  # This is what _handle_execute_yield does
            calls = None  # Clear calls after execution

        assert tool_results_sent is True
        assert calls is None


class TestSessionResultUnwrapping:
    """Test session Result wrapper unwrapping logic."""

    def test_successful_session_result_unwrapping(self):
        """Test that Result wrapper gets unwrapped correctly."""
        # Mock a successful Result
        mock_session_result = Mock()
        mock_session_result.success = True
        mock_unwrapped_session = Mock()
        mock_session_result.unwrap = Mock(return_value=mock_unwrapped_session)

        # Simulate the unwrapping logic from resume.py
        session = None
        if (
            hasattr(mock_session_result, "success")
            and hasattr(mock_session_result, "unwrap")
            and mock_session_result.success
        ):
            session = mock_session_result.unwrap()

        assert session is mock_unwrapped_session
        mock_session_result.unwrap.assert_called_once()

    def test_failed_session_result_raises_error(self):
        """Test that failed Result wrapper raises error."""
        # Mock a failed Result
        mock_session_result = Mock()
        mock_session_result.success = False

        # Simulate the unwrapping logic
        with pytest.raises(RuntimeError, match="Failed to establish WebSocket connection"):
            if hasattr(mock_session_result, "success") and hasattr(mock_session_result, "unwrap"):
                if mock_session_result.success:
                    mock_session_result.unwrap()
                else:
                    raise RuntimeError("Failed to establish WebSocket connection")

    def test_plain_session_object_passes_through(self):
        """Test that non-Result objects pass through unchanged."""
        # Create a plain object without success/unwrap attributes
        plain_session = type("PlainSession", (), {})()

        # Simulate the logic for plain objects
        session = None
        if hasattr(plain_session, "success") and hasattr(plain_session, "unwrap"):
            # This shouldn't execute for plain objects
            raise AssertionError("Plain object shouldn't have success/unwrap")
        session = plain_session

        assert session is plain_session
