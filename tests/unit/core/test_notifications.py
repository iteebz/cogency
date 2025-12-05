"""Test notification infrastructure contracts."""

import pytest

from cogency import Agent
from cogency.lib.sqlite import default_storage


@pytest.fixture
def storage():
    return default_storage(":memory:")


@pytest.mark.asyncio
async def test_notifications_none_backward_compat(storage):
    """Default notifications=None preserves existing behavior."""
    agent = Agent(llm="openai", storage=storage, notifications=None)

    async for event in agent("Hello"):
        if event["type"] == "end":
            break


@pytest.mark.asyncio
async def test_notifications_called_per_iteration(storage):
    """Notifications polled once per iteration."""
    call_count = 0

    async def notifications():
        nonlocal call_count
        call_count += 1
        return [f"Notification {call_count}"]

    agent = Agent(llm="openai", storage=storage, notifications=notifications, max_iterations=2)

    async for event in agent("Hello"):
        if event["type"] == "end":
            break

    assert call_count >= 1


@pytest.mark.asyncio
async def test_notifications_failure_continues(storage):
    """Notification source failure doesn't break agent loop."""

    async def failing_notifications():
        raise RuntimeError("Notification source failed")

    agent = Agent(llm="openai", storage=storage, notifications=failing_notifications)

    # Should complete without raising
    async for event in agent("Hello"):
        if event["type"] == "end":
            break


@pytest.mark.asyncio
async def test_notifications_empty_list(storage):
    """Empty notification list is valid."""

    async def empty_notifications():
        return []

    agent = Agent(llm="openai", storage=storage, notifications=empty_notifications)

    async for event in agent("Hello"):
        if event["type"] == "end":
            break
