"""Test State notification functionality (formerly Output)."""

from unittest.mock import AsyncMock

import pytest

from cogency.context import Context
from cogency.state import State


def mock_context():
    return Context("test")


@pytest.mark.asyncio
async def test_stream_functionality():
    """Test streaming functionality in State."""
    callback = AsyncMock()
    context = mock_context()
    state = State(context=context, query="test query", verbose=True, callback=callback)

    await state.notify("test_event", {"message": "test data"})

    # Check that the stream was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "test_event"
    assert entry["data"] == {"message": "test data"}
    assert entry["iteration"] == 0

    # Check that callback was called
    callback.assert_called_once_with("{'message': 'test data'}")


@pytest.mark.asyncio
async def test_stream_without_verbose():
    """Test that streaming doesn't call callback when verbose=False."""
    callback = AsyncMock()
    context = mock_context()
    state = State(context=context, query="test query", verbose=False, callback=callback)

    await state.notify("test_event", {"message": "test data"})

    # Notification should still be recorded
    assert len(state.notifications) == 1

    # But callback should not be called
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_state_change_streaming():
    """Test state change streaming."""
    callback = AsyncMock()
    context = mock_context()
    state = State(context=context, query="test query", verbose=True, callback=callback)

    await state.notify("state_change", {"state": "reasoning", "mode": "fast"})

    # Check notification was recorded with correct structure
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "state_change"
    assert entry["data"] == {"state": "reasoning", "mode": "fast"}


@pytest.mark.asyncio
async def test_reasoning_streaming():
    """Test reasoning content streaming."""
    callback = AsyncMock()
    context = mock_context()
    state = State(context=context, query="test query", verbose=True, callback=callback)

    await state.notify("reasoning", {"content": "I need to search for information"})

    # Check notification was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "reasoning"
    assert entry["data"] == {"content": "I need to search for information"}


@pytest.mark.asyncio
async def test_action_streaming():
    """Test action execution streaming."""
    callback = AsyncMock()
    context = mock_context()
    state = State(context=context, query="test query", verbose=True, callback=callback)

    action_data = {"tool": "search", "args": {"query": "test"}}
    await state.notify("action", action_data)

    # Check notification was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "action"
    assert entry["data"] == action_data


@pytest.mark.asyncio
async def test_response_streaming():
    """Test final response streaming."""
    callback = AsyncMock()
    context = mock_context()
    state = State(context=context, query="test query", verbose=True, callback=callback)

    await state.notify("response", {"text": "Here is my final response"})

    # Check notification was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "response"
    assert entry["data"] == {"text": "Here is my final response"}


@pytest.mark.asyncio
async def test_no_callback():
    """Test streaming when no callback is provided."""
    context = mock_context()
    state = State(context=context, query="test query", verbose=True)

    # Should not raise error
    await state.notify("test_event", {"message": "test data"})

    # Notification should still be recorded
    assert len(state.notifications) == 1


@pytest.mark.asyncio
async def test_callback_function_vs_coroutine():
    """Test that both sync and async callbacks work."""

    # Test with sync callback
    def sync_callback(x):
        pass

    context = mock_context()
    state = State(context=context, query="test query", verbose=True, callback=sync_callback)

    # Should not raise error
    await state.notify("test_event", {"message": "test data"})
    assert len(state.notifications) == 1

    # Test with async callback
    async_callback = AsyncMock()
    state.callback = async_callback

    await state.notify("test_event2", {"message": "test data 2"})
    async_callback.assert_called_once()
