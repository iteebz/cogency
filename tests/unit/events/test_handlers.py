"""Unit tests for event handlers."""

from collections import deque
from io import StringIO
from unittest.mock import patch

import pytest

from cogency.events.console import ConsoleHandler
from cogency.events.handlers import EventBuffer


class TestConsoleHandler:
    """Test ConsoleHandler outputs and behavior."""

    def test_disabled_handler_outputs_nothing(self):
        handler = ConsoleHandler(enabled=False)

        with patch("builtins.print") as mock_print:
            handler.handle({"type": "start", "data": {"query": "test"}, "timestamp": 123})
            mock_print.assert_not_called()

    def test_start_event_with_query(self):
        handler = ConsoleHandler(enabled=True)

        with patch("builtins.print") as mock_print:
            handler.handle({"type": "start", "data": {"query": "Hello world"}, "timestamp": 123})

            mock_print.assert_called_once_with("> Hello world")

    def test_agent_create_complete(self):
        handler = ConsoleHandler(enabled=True)

        with patch("builtins.print") as mock_print:
            handler.handle(
                {
                    "type": "agent_create",
                    "data": {"name": "test_agent", "status": "complete"},
                    "timestamp": 123,
                }
            )
            # agent_create events are no longer handled (not in cli.md spec)
            mock_print.assert_not_called()

    def test_tool_success_with_duration(self):
        handler = ConsoleHandler(enabled=True)

        with patch("builtins.print") as mock_print:
            handler.handle(
                {
                    "type": "tool",
                    "data": {"name": "search", "ok": True, "duration": 1.5},
                    "timestamp": 123,
                }
            )
            mock_print.assert_called_once_with("✓ Search completed")

    def test_error_event(self):
        handler = ConsoleHandler(enabled=True)

        with patch("builtins.print") as mock_print:
            handler.handle(
                {"type": "error", "data": {"message": "Something went wrong"}, "timestamp": 123}
            )
            mock_print.assert_called_once_with("✗ Something went wrong")

    def test_debug_event_only_when_debug_enabled(self):
        handler_debug = ConsoleHandler(enabled=True, debug=True)
        handler_no_debug = ConsoleHandler(enabled=True, debug=False)

        event = {"type": "debug", "data": {"message": "Debug info"}, "timestamp": 123}

        with patch("builtins.print") as mock_print:
            handler_debug.handle(event)
            mock_print.assert_called_once_with("[DEBUG] Debug info")

            mock_print.reset_mock()
            handler_no_debug.handle(event)
            mock_print.assert_not_called()


class TestEventBuffer:
    """Test EventBuffer event storage and filtering."""

    def test_stores_events(self):
        buffer = EventBuffer(max_size=10)

        event = {"type": "start", "data": {"query": "test"}, "timestamp": 123.45}
        buffer.handle(event)

        logs = buffer.logs()
        assert len(logs) == 1
        assert logs[0] == event

    def test_filters_by_type(self):
        buffer = EventBuffer(max_size=10)

        # Add different event types
        buffer.handle({"type": "start", "data": {"query": "test"}, "timestamp": 123})
        buffer.handle({"type": "tool", "data": {"name": "search"}, "timestamp": 124})
        buffer.handle({"type": "error", "data": {"message": "failed"}, "timestamp": 125})
        buffer.handle({"type": "tool", "data": {"name": "http"}, "timestamp": 126})

        # Filter by type
        tool_logs = buffer.logs(type="tool")
        assert len(tool_logs) == 2
        assert all(log["type"] == "tool" for log in tool_logs)

        error_logs = buffer.logs(type="error")
        assert len(error_logs) == 1
        assert error_logs[0]["type"] == "error"

    def test_errors_only_filtering(self):
        buffer = EventBuffer(max_size=10)

        # Add mixed events
        buffer.handle({"type": "start", "data": {"query": "test"}, "timestamp": 123})
        buffer.handle({"type": "error", "data": {"message": "fail"}, "timestamp": 124})
        buffer.handle({"type": "tool", "status": "error", "timestamp": 125})

        error_logs = buffer.logs(errors_only=True)
        assert len(error_logs) == 2

    def test_max_size_rolling_buffer(self):
        buffer = EventBuffer(max_size=2)

        buffer.handle({"type": "event1", "timestamp": 1})
        buffer.handle({"type": "event2", "timestamp": 2})
        buffer.handle({"type": "event3", "timestamp": 3})

        logs = buffer.logs()
        assert len(logs) == 2
        assert logs[0]["type"] == "event2"
        assert logs[1]["type"] == "event3"
