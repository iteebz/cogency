"""Test event bus logging via agent.logs()."""

import pytest

from cogency import Agent
from cogency.events import MessageBus, init_bus
from cogency.events.handlers import EventBuffer
from tests.fixtures.provider import MockLLM


@pytest.fixture(autouse=True)
def reset_event_bus():
    """Reset event bus before each test."""
    # Create fresh bus with logger handler
    bus = MessageBus()
    handler = EventBuffer()
    bus.subscribe(handler)
    init_bus(bus)
    yield


def test_after_execution():
    """Test that logs method works and captures events."""
    from cogency.events import emit

    agent = Agent("test", llm=MockLLM(), tools=[])

    # Emit some test events to verify logging works
    emit("test", message="test message")
    emit("agent", operation="test")

    # Should be able to retrieve logs
    logs = agent.logs()
    assert isinstance(logs, list)

    # Should capture emitted events
    test_events = [log for log in logs if log.get("type") == "test"]
    agent_events = [log for log in logs if log.get("type") == "agent"]

    assert len(test_events) >= 1
    assert len(agent_events) >= 1
    assert test_events[0]["message"] == "test message"


@pytest.mark.asyncio
async def test_logging_during_run():
    """Test that events are logged during agent.run execution."""
    agent = Agent("test", tools=[])
    # Agent constructor uses detect_llm() which is auto-mocked by conftest.py

    # Run agent - this should generate events
    await agent.run("test query")

    # Should have captured execution events
    logs = agent.logs()
    assert len(logs) > 0

    # Should have agent execution events
    agent_events = [log for log in logs if log.get("type") == "agent"]
    assert len(agent_events) > 0


def test_log_filtering():
    """Test log filtering capabilities."""
    from cogency.events import emit

    agent = Agent("test", llm=MockLLM(), tools=[])

    # Emit various event types
    emit("debug", message="debug info")
    emit("error", message="error occurred", level="ERROR")
    emit("info", message="info message")

    # Test filtering by type
    debug_logs = agent.logs(type="debug")
    error_logs = agent.logs(type="error")

    debug_events = [log for log in debug_logs if log.get("type") == "debug"]
    error_events = [log for log in error_logs if log.get("type") == "error"]

    assert len(debug_events) >= 1
    assert len(error_events) >= 1
    assert debug_events[0]["message"] == "debug info"
    assert error_events[0]["message"] == "error occurred"


def test_empty_logs():
    """Test behavior when no events have been emitted."""
    agent = Agent("test", llm=MockLLM(), tools=[])

    # Fresh agent should have no logs initially
    logs = agent.logs()

    # May have some initialization events, but should be a list
    assert isinstance(logs, list)
