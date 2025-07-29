"""Test State notification functionality (formerly Output)."""

from unittest.mock import AsyncMock

import pytest

from cogency.state import State
from cogency.utils.notify import notify


@pytest.mark.asyncio
async def test_stream_functionality():
    """Test streaming functionality in State."""
    callback = AsyncMock()
    state = State(query="test query", verbose=True, callback=callback)

    await notify(state, "test_event", {"message": "test data"})

    # Check that the stream was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "test_event"
    assert entry["data"] == {"message": "test data"}
    assert entry["iteration"] == 0

    # Check that callback was called
    callback.assert_called_once_with("test_event: {'message': 'test data'}")


@pytest.mark.asyncio
async def test_stream_without_verbose():
    """Test that streaming doesn't call callback when verbose=False."""
    callback = AsyncMock()
    state = State(query="test query", verbose=False, callback=callback)

    await notify(state, "test_event", {"message": "test data"})

    # Notification should still be recorded
    assert len(state.notifications) == 1

    # But callback should not be called
    callback.assert_not_called()


@pytest.mark.asyncio
async def test_reason_phase_streaming():
    """Test reason phase streaming."""
    callback = AsyncMock()
    state = State(query="test query", verbose=True, callback=callback)

    await notify(state, "reason", {"state": "reasoning", "mode": "fast"})

    # Check notification was recorded with correct structure
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "reason"
    assert entry["data"] == {"state": "reasoning", "mode": "fast"}


@pytest.mark.asyncio
async def test_preprocess_phase_streaming():
    """Test preprocess phase streaming."""
    callback = AsyncMock()
    state = State(query="test query", verbose=True, callback=callback)

    await notify(state, "preprocess", {"content": "Setting up tools and memory"})

    # Check notification was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "preprocess"
    assert entry["data"] == {"content": "Setting up tools and memory"}


@pytest.mark.asyncio
async def test_action_streaming():
    """Test action execution streaming."""
    callback = AsyncMock()
    state = State(query="test query", verbose=True, callback=callback)

    action_data = {"tool": "search", "args": {"query": "test"}}
    await notify(state, "action", action_data)

    # Check notification was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "action"
    assert entry["data"] == action_data


@pytest.mark.asyncio
async def test_respond_phase_streaming():
    """Test respond phase streaming."""
    callback = AsyncMock()
    state = State(query="test query", verbose=True, callback=callback)

    await notify(state, "respond", {"text": "Here is my final response"})

    # Check notification was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "respond"
    assert entry["data"] == {"text": "Here is my final response"}


@pytest.mark.asyncio
async def test_trace_streaming():
    """Test trace streaming for debug information."""
    callback = AsyncMock()
    state = State(query="test query", verbose=True, callback=callback)

    await notify(state, "trace", {"message": "Debug info", "phase": "reason"})

    # Check notification was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "trace"
    assert entry["data"] == {"message": "Debug info", "phase": "reason"}


@pytest.mark.asyncio
async def test_no_callback():
    """Test streaming when no callback is provided."""
    state = State(query="test query", verbose=True)

    # Should not raise error
    await notify(state, "test_event", {"message": "test data"})

    # Notification should still be recorded
    assert len(state.notifications) == 1


@pytest.mark.asyncio
async def test_callback_function_vs_coroutine():
    """Test that both sync and async callbacks work."""

    # Test with sync callback
    def sync_callback(x):
        pass

    state = State(query="test query", verbose=True, callback=sync_callback)

    # Should not raise error
    await notify(state, "test_event", {"message": "test data"})
    assert len(state.notifications) == 1

    # Test with async callback
    async_callback = AsyncMock()
    state.callback = async_callback

    await notify(state, "test_event2", {"message": "test data 2"})
    async_callback.assert_called_once_with("test_event2: {'message': 'test data 2'}")
