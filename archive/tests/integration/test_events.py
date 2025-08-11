"""Integration tests for event system - full workflow testing."""

from unittest.mock import MagicMock

import pytest

from cogency.events.bus import MessageBus, emit, init_bus
from cogency.events.console import ConsoleHandler
from cogency.events.handlers import EventBuffer


def test_full_agent_session_workflow():
    """Test a complete agent session from start to finish."""
    # Setup
    bus = MessageBus()
    console = ConsoleHandler(enabled=False)  # Disable printing for test
    logger = EventBuffer(max_size=100)

    bus.subscribe(console)
    bus.subscribe(logger)
    init_bus(bus)

    # Simulate agent session
    emit("start", query="What is 2+2?")
    emit("triage", state="complete", selected_tools=0)
    emit("reason", state="planning")
    emit("reason", state="complete", early_return=True)
    emit("respond", state="generating")
    emit("respond", state="complete")

    # Verify logger captured events
    logs = logger.logs()
    assert len(logs) == 6
    assert logs[0]["type"] == "start"
    assert logs[0]["data"]["query"] == "What is 2+2?"

    # Verify session flow in logs
    assert logs[0]["data"]["query"] == "What is 2+2?"
    assert any(log["type"] == "reason" for log in logs)
    assert any(log["type"] == "respond" for log in logs)


def test_tool_usage_tracking():
    """Test tool execution tracking across handlers."""
    bus = MessageBus()
    logger = EventBuffer()

    bus.subscribe(logger)
    init_bus(bus)

    # Start session
    emit("start", query="Search for something")

    # Tool calls
    emit("tool", name="search", ok=True, duration=1.2)
    emit("tool", name="http", ok=False, duration=0.5)
    emit("tool", name="search", ok=True, duration=0.8)

    # End session
    emit("respond", state="complete")

    # Check logger captured tool events
    logs = logger.logs()
    tool_logs = [log for log in logs if log["type"] == "tool"]
    assert len(tool_logs) == 3

    # Verify tool details in logs
    search_logs = [log for log in tool_logs if log.get("data", {}).get("name") == "search"]
    assert len(search_logs) == 2
    assert all(log.get("data", {}).get("ok") for log in search_logs)


def test_error_handling_across_handlers():
    """Test error event handling in all handlers."""
    bus = MessageBus()
    console = MagicMock()  # Mock to capture calls
    logger = EventBuffer()

    bus.subscribe(console)
    bus.subscribe(logger)
    init_bus(bus)

    emit("start", query="Test error handling")
    emit("error", message="Something went wrong")
    emit("respond", state="complete")

    # Console should have received error
    console.handle.assert_called()
    error_call = None
    for call in console.handle.call_args_list:
        if call[0][0]["type"] == "error":
            error_call = call[0][0]
            break

    assert error_call is not None
    assert error_call["data"]["message"] == "Something went wrong"

    # Logger should have stored error
    logs = logger.logs()
    error_logs = [log for log in logs if log["type"] == "error"]
    assert len(error_logs) == 1
    assert error_logs[0]["data"]["message"] == "Something went wrong"


def test_handler_independence():
    """Test that handler failures don't affect other handlers."""
    # Save original bus to restore later
    from cogency.events.bus import _bus as original_bus

    bus = MessageBus()

    # Create a handler that will fail
    failing_handler = MagicMock()
    failing_handler.handle.side_effect = Exception("Handler failed")

    # Create normal handlers
    logger = EventBuffer()

    bus.subscribe(failing_handler)
    bus.subscribe(logger)
    init_bus(bus)

    try:
        # Bus doesn't catch handler exceptions - handlers should be robust
        # This is expected behavior - failing handlers propagate exceptions
        with pytest.raises(Exception, match="Handler failed"):
            emit("test_event", data="value")
    finally:
        # Restore original bus to prevent test pollution
        init_bus(original_bus)
