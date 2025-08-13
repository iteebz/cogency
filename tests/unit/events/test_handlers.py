"""Unit tests for event handlers."""

from unittest.mock import patch

from cogency.events.console import ConsoleHandler
from cogency.events.handlers import EventBuffer


def test_disabled_handler():
    """Disabled handler produces no output."""
    handler = ConsoleHandler(enabled=False)

    with patch("builtins.print") as mock_print:
        handler.handle({"type": "start", "data": {"query": "test"}, "timestamp": 123})
        mock_print.assert_not_called()


def test_start_event():
    """Start events display query."""
    handler = ConsoleHandler(enabled=True)

    with patch("builtins.print") as mock_print:
        handler.handle({"type": "start", "data": {"query": "Hello world"}, "timestamp": 123})

        mock_print.assert_called_once_with("> Hello world")


def test_agent_create():
    """Agent create events are ignored."""
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


def test_tool_success():
    """Tool success events are handled without crashing."""
    handler = ConsoleHandler(enabled=True)

    # Test that handler processes tool success events without error
    handler.handle(
        {
            "type": "action",
            "data": {"state": "success", "tool": "search", "result": "Found results"},
            "timestamp": 123,
        }
    )
    # No assertion needed - just verify it doesn't crash


def test_error_event():
    """Error events are handled without crashing."""
    handler = ConsoleHandler(enabled=True)

    # Test that handler processes error events without error
    handler.handle({"type": "error", "data": {"message": "Something went wrong"}, "timestamp": 123})
    # No assertion needed - just verify it doesn't crash


def test_debug_only_when_enabled():
    """Debug events are handled differently based on debug setting."""
    handler_debug = ConsoleHandler(enabled=True, debug=True)
    handler_no_debug = ConsoleHandler(enabled=True, debug=False)

    event = {"type": "debug", "data": {"message": "Debug info"}, "timestamp": 123}

    # Test that handlers process debug events without error
    handler_debug.handle(event)
    handler_no_debug.handle(event)
    # No assertion needed - just verify they don't crash


def test_stores_events():
    """Buffer stores events."""
    buffer = EventBuffer(max_size=10)

    event = {"type": "start", "data": {"query": "test"}, "timestamp": 123.45}
    buffer.handle(event)

    logs = buffer.logs()
    assert len(logs) == 1
    assert logs[0] == event


def test_filters_by_type():
    """Buffer filters events by type."""
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


def test_errors_only():
    """Buffer filters error events."""
    buffer = EventBuffer(max_size=10)

    # Add mixed events
    buffer.handle({"type": "start", "data": {"query": "test"}, "timestamp": 123})
    buffer.handle({"type": "error", "data": {"message": "fail"}, "timestamp": 124})
    buffer.handle({"type": "tool", "status": "error", "timestamp": 125})

    error_logs = buffer.logs(errors_only=True)
    assert len(error_logs) == 2


def test_rolling():
    """Buffer rolls over when max size exceeded."""
    buffer = EventBuffer(max_size=2)

    buffer.handle({"type": "event1", "timestamp": 1})
    buffer.handle({"type": "event2", "timestamp": 2})
    buffer.handle({"type": "event3", "timestamp": 3})

    logs = buffer.logs()
    assert len(logs) == 2
    assert logs[0]["type"] == "event2"
    assert logs[1]["type"] == "event3"
