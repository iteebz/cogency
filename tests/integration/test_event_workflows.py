"""Event system workflow integration - observability validation."""

from unittest.mock import MagicMock, Mock

from cogency.events.bus import MessageBus, emit, init_bus
from cogency.events.console import ConsoleHandler
from cogency.events.handlers import EventBuffer


def test_agent_session_event_workflow():
    """Test complete agent session event emission flow."""
    # Setup event system
    bus = MessageBus()
    console = ConsoleHandler(enabled=False)  # Disable output for test
    buffer = EventBuffer(max_size=50)

    bus.subscribe(console)
    bus.subscribe(buffer)
    init_bus(bus)

    # Simulate agent session workflow
    emit("start", query="What is machine learning?")
    emit("triage", state="analyzing", tools_selected=2)
    emit("reason", state="planning")
    emit("tool", name="search", success=True, duration=1.5)
    emit("reason", state="synthesis")
    emit("respond", state="generating")
    emit("respond", state="complete")

    # Verify workflow captured
    logs = buffer.logs()
    assert len(logs) == 7

    # Verify session progression
    event_types = [log["type"] for log in logs]
    expected_flow = ["start", "triage", "reason", "tool", "reason", "respond", "respond"]
    assert event_types == expected_flow

    # Verify start event details
    start_event = logs[0]
    assert start_event["data"]["query"] == "What is machine learning?"

    # Verify tool execution tracking
    tool_event = logs[3]
    assert tool_event["data"]["name"] == "search"
    assert tool_event["data"]["success"] is True
    assert tool_event["data"]["duration"] == 1.5


def test_multi_tool_execution_tracking():
    """Test tool usage tracking across multiple executions."""
    bus = MessageBus()
    buffer = EventBuffer()

    bus.subscribe(buffer)
    init_bus(bus)

    # Start session
    emit("start", query="Complex analysis task")

    # Multiple tool executions
    emit("tool", name="files", success=True, duration=0.3)
    emit("tool", name="search", success=False, duration=2.1, error="Timeout")
    emit("tool", name="files", success=True, duration=0.5)
    emit("tool", name="shell", success=True, duration=1.2)

    # End session
    emit("respond", state="complete")

    # Analyze tool usage
    logs = buffer.logs()
    tool_events = [log for log in logs if log["type"] == "tool"]
    assert len(tool_events) == 4

    # Verify tool success/failure tracking
    successful_tools = [e for e in tool_events if e["data"]["success"]]
    failed_tools = [e for e in tool_events if not e["data"]["success"]]

    assert len(successful_tools) == 3
    assert len(failed_tools) == 1
    assert failed_tools[0]["data"]["error"] == "Timeout"

    # Verify tool frequency
    files_calls = [e for e in tool_events if e["data"]["name"] == "files"]
    assert len(files_calls) == 2


def test_error_handling_workflow():
    """Test error event handling across handlers."""
    bus = MessageBus()
    console = MagicMock()
    buffer = EventBuffer()

    bus.subscribe(console)
    bus.subscribe(buffer)
    init_bus(bus)

    # Simulate session with error
    emit("start", query="Error test")
    emit("reason", state="processing")
    emit("error", message="LLM provider timeout", component="provider")
    emit("respond", state="error_recovery")

    # Verify console handler received error
    console.handle.assert_called()
    error_calls = [call for call in console.handle.call_args_list if call[0][0]["type"] == "error"]
    assert len(error_calls) == 1

    error_event = error_calls[0][0][0]
    assert error_event["data"]["message"] == "LLM provider timeout"
    assert error_event["data"]["component"] == "provider"

    # Verify buffer stored error
    logs = buffer.logs()
    error_logs = [log for log in logs if log["type"] == "error"]
    assert len(error_logs) == 1
    assert error_logs[0]["data"]["message"] == "LLM provider timeout"


def test_event_handler_isolation():
    """Test handlers operate independently without interference."""
    bus = MessageBus()

    # Create handlers with different behaviors
    buffer1 = EventBuffer(max_size=10)
    buffer2 = EventBuffer(max_size=5)

    bus.subscribe(buffer1)
    bus.subscribe(buffer2)
    init_bus(bus)

    # Generate events
    for i in range(8):
        emit("test", iteration=i)

    # Verify independent operation
    logs1 = buffer1.logs()
    logs2 = buffer2.logs()

    assert len(logs1) == 8  # Buffer1 has capacity for all
    assert len(logs2) == 5  # Buffer2 limited by max_size

    # Both should have same event structure
    for log in logs1[:5]:
        assert log["type"] == "test"
        assert "iteration" in log["data"]


def test_session_state_tracking():
    """Test session state progression through events."""
    bus = MessageBus()
    buffer = EventBuffer()

    bus.subscribe(buffer)
    init_bus(bus)

    # Complex session with state transitions
    emit("start", query="Multi-step task")
    emit("triage", state="analyzing", complexity="high")
    emit("reason", state="planning", step=1)
    emit("reason", state="execution", step=2)
    emit("tool", name="search", success=True, duration=1.0)
    emit("reason", state="synthesis", step=3)
    emit("respond", state="generating")
    emit("respond", state="complete", tokens_generated=150)

    logs = buffer.logs()

    # Verify state progression
    reason_events = [log for log in logs if log["type"] == "reason"]
    states = [event["data"]["state"] for event in reason_events]
    expected_states = ["planning", "execution", "synthesis"]
    assert states == expected_states

    # Verify final completion
    respond_events = [log for log in logs if log["type"] == "respond"]
    final_event = respond_events[-1]
    assert final_event["data"]["state"] == "complete"
    assert final_event["data"]["tokens_generated"] == 150


def test_event_bus_subscription_contract():
    """Test event bus subscription and unsubscription contracts."""
    bus = MessageBus()
    handler1 = Mock()
    handler2 = Mock()

    # Test subscription
    bus.subscribe(handler1)
    bus.subscribe(handler2)
    assert len(bus.handlers) == 2

    # Test event distribution
    init_bus(bus)
    emit("test", data="value")

    handler1.handle.assert_called_once()
    handler2.handle.assert_called_once()

    # Verify both handlers received same event
    event1 = handler1.handle.call_args[0][0]
    event2 = handler2.handle.call_args[0][0]
    assert event1["type"] == event2["type"] == "test"
    assert event1["data"] == event2["data"] == {"data": "value"}
