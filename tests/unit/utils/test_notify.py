"""Test Agent notification callback functionality."""

from unittest.mock import AsyncMock

import pytest

from cogency.agent import Agent
from cogency.state import State


@pytest.mark.asyncio
async def test_notification_callback():
    """Test Agent notification callback functionality."""
    callback = AsyncMock()
    state = State(query="test query", notify=True, callback=callback)
    
    # Create an agent to test the callback pattern
    agent = Agent()
    notify = agent._notify_cb(state)
    
    # Test callback notification
    notify("test_event", "test message")
    
    # Allow async task to complete
    import asyncio
    await asyncio.sleep(0.01)
    
    # Check that callback was called
    callback.assert_called_once_with("test message")
    
    # Check that notification was recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "test_event"
    assert entry["message"] == "test message"
    assert entry["iteration"] == 0


@pytest.mark.asyncio
async def test_notification_without_callback():
    """Test that notifications work without a callback."""
    state = State(query="test query", notify=False, callback=None)
    
    agent = Agent()
    notify = agent._notify_cb(state)
    
    # Should not raise error
    notify("test_event", "test message")
    
    # Allow async task to complete
    import asyncio
    await asyncio.sleep(0.01)
    
    # Notification should still be recorded
    assert len(state.notifications) == 1
    entry = state.notifications[0]
    assert entry["event_type"] == "test_event"
    assert entry["message"] == "test message"


@pytest.mark.asyncio 
async def test_notification_disabled():
    """Test that callback is not called when notify=False."""
    callback = AsyncMock()
    state = State(query="test query", notify=False, callback=callback)
    
    agent = Agent()
    notify = agent._notify_cb(state)
    
    notify("test_event", "test message")
    
    # Allow async task to complete
    import asyncio
    await asyncio.sleep(0.01)
    
    # Notification should still be recorded
    assert len(state.notifications) == 1
    
    # But callback should not be called since notify=False
    callback.assert_not_called()
