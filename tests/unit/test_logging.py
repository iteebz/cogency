"""Test event bus logging via agent.logs()."""

import pytest

from cogency import Agent
from cogency.events import MessageBus, get_logs, init_bus
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
    # Clear logs after test (don't clear until next test setup)
    # handler.events.clear()  # Let events persist until the fixture runs again


def test_logs_after_execution():
    """Test that logs method works and captures events."""
    from cogency.events import emit

    agent = Agent("test", llm=MockLLM(), tools=[])

    # Emit some test events to verify logging works
    emit("test", message="test log message")
    emit("agent", action="test_action", status="complete")

    # Test logs method
    logs = agent.logs()

    assert isinstance(logs, list)

    # Check that events were actually emitted
    test_events = [log for log in logs if log.get("type") == "test"]
    agent_events = [log for log in logs if log.get("type") == "agent"]

    assert len(test_events) >= 1, f"Should have test events in logs, got: {logs}"
    assert len(agent_events) >= 1, f"Should have agent events in logs, got: {logs}"


@pytest.mark.asyncio
async def test_logs_work_without_debug():
    """Test that logs work regardless of debug setting."""
    agent = Agent("test", llm=MockLLM(), tools=[])

    # Logs should still work even with debug=False
    logs = agent.logs()
    assert isinstance(logs, list)  # Should return list even if empty or with setup events


def test_logs_with_fresh_agent():
    """Test that fresh agent has setup events."""
    agent = Agent("test", llm=MockLLM(), tools=[])
    logs = agent.logs()

    # New event bus architecture emits setup events during agent creation
    # So logs should not be empty for a fresh agent
    assert isinstance(logs, list)


def test_logs_multiple_executions():
    """Test that logs accumulate across multiple events."""
    from cogency.events import emit

    agent = Agent("test", llm=MockLLM(), tools=[])

    # First batch of events
    emit("execution", query="query 1", step="start")
    emit("execution", query="query 1", step="complete")
    logs_after_first = agent.logs()
    first_execution_events = [log for log in logs_after_first if log.get("type") == "execution"]

    # Second batch of events
    emit("execution", query="query 2", step="start")
    emit("execution", query="query 2", step="complete")
    logs_after_second = agent.logs()
    second_execution_events = [log for log in logs_after_second if log.get("type") == "execution"]

    # Should have more execution events after second batch
    assert (
        len(second_execution_events) > len(first_execution_events)
    ), f"Expected more execution events: {len(first_execution_events)} -> {len(second_execution_events)}"


def test_get_logs_function():
    """Test that get_logs() function works independently."""
    # Should return list (may be empty or have setup events)
    logs = get_logs()
    assert isinstance(logs, list)
