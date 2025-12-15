"""Test notification infrastructure contracts."""

import pytest

from cogency import Agent


@pytest.mark.asyncio
async def test_notifications_none_backward_compat(mock_llm, mock_storage):
    """Default notifications=None preserves existing behavior."""
    mock_llm.set_response_tokens(["Response\n<end>"])
    agent = Agent(llm=mock_llm, storage=mock_storage, notifications=None, mode="replay")

    async for event in agent("Hello"):
        if event["type"] == "end":
            break


@pytest.mark.asyncio
async def test_notifications_called_per_iteration(mock_llm, mock_storage):
    """Notifications polled once per iteration."""
    call_count = 0

    async def notifications():
        nonlocal call_count
        call_count += 1
        return [f"Notification {call_count}"]

    mock_llm.set_response_tokens(["Response\n<end>"])
    agent = Agent(
        llm=mock_llm,
        storage=mock_storage,
        notifications=notifications,
        max_iterations=2,
        mode="replay",
    )

    async for event in agent("Hello"):
        if event["type"] == "end":
            break

    assert call_count >= 1


@pytest.mark.asyncio
async def test_notifications_failure_continues(mock_llm, mock_storage):
    """Notification source failure doesn't break agent loop."""

    async def failing_notifications():
        raise RuntimeError("Notification source failed")

    mock_llm.set_response_tokens(["Response\n<end>"])
    agent = Agent(
        llm=mock_llm, storage=mock_storage, notifications=failing_notifications, mode="replay"
    )

    # Should complete without raising
    async for event in agent("Hello"):
        if event["type"] == "end":
            break


@pytest.mark.asyncio
async def test_notifications_empty_list(mock_llm, mock_storage):
    """Empty notification list is valid."""

    async def empty_notifications():
        return []

    mock_llm.set_response_tokens(["Response\n<end>"])
    agent = Agent(
        llm=mock_llm, storage=mock_storage, notifications=empty_notifications, mode="replay"
    )

    async for event in agent("Hello"):
        if event["type"] == "end":
            break
