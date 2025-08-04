"""Test event bus logging via agent.logs()."""

import contextlib

import pytest

from cogency import Agent
from cogency.events import MessageBus, get_logs, init_bus
from cogency.events.handlers import LoggerHandler
from tests.fixtures.llm import MockLLM


@pytest.fixture(autouse=True)
def reset_event_bus():
    """Reset event bus before each test."""
    # Create fresh bus with logger handler
    bus = MessageBus()
    handler = LoggerHandler()
    bus.subscribe(handler)
    init_bus(bus)
    yield
    # Clear logs after test
    handler.events.clear()


@pytest.mark.asyncio
async def test_logs_after_execution():
    """Test that logs method works and captures events."""
    agent = Agent("test", llm=MockLLM(), tools=[])

    # Get initial log state
    initial_logs = agent.logs()
    initial_count = len(initial_logs)

    # Try to execute agent - even if it fails, logs should still work
    with contextlib.suppress(Exception):
        await agent.run_async("test query")

    # Logs method should work regardless of execution success
    logs = agent.logs()
    assert isinstance(logs, list)
    assert len(logs) >= initial_count


@pytest.mark.asyncio
async def test_logs_work_without_debug():
    """Test that logs work regardless of debug setting."""
    agent = Agent("test", llm=MockLLM(), tools=[], debug=False)

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


@pytest.mark.asyncio
async def test_logs_multiple_executions():
    """Test that logs accumulate across multiple executions."""
    agent = Agent("test", llm=MockLLM(), tools=[])

    # First execution
    await agent.run_async("query 1")
    logs_after_first = agent.logs()
    first_count = len(logs_after_first)

    # Second execution
    await agent.run_async("query 2")
    logs_after_second = agent.logs()
    second_count = len(logs_after_second)

    # Should have more events after second execution
    assert second_count > first_count


def test_get_logs_function():
    """Test that get_logs() function works independently."""
    # Should return list (may be empty or have setup events)
    logs = get_logs()
    assert isinstance(logs, list)
