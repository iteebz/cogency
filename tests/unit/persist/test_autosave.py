"""Tests for autosave persistence - Database as State."""

import asyncio
from unittest.mock import AsyncMock, Mock

import pytest

from cogency.state import AgentState


@pytest.fixture
def mock_store():
    """Mock store for testing write-through behavior."""
    store = AsyncMock()
    store.save = AsyncMock(return_value=True)
    return store


def test_agent_state_auto_creates_store():
    """Test AgentState automatically creates SQLite store."""
    state = AgentState("test query")

    assert state.store is not None
    assert hasattr(state.store, "save")


def test_execution_add_message_writes_through(mock_store):
    """Test add_message triggers immediate persistence."""
    state = AgentState("test query")
    state.store = mock_store

    # Mock the persist method to track calls
    state.persist = Mock()

    state.execution.add_message("user", "hello")

    # Should trigger write-through
    state.persist.assert_called_once()


def test_reasoning_learn_writes_through(mock_store):
    """Test learn() triggers immediate persistence."""
    state = AgentState("test query")
    state.store = mock_store

    state.persist = Mock()

    state.reasoning.learn("New insight")

    # Should trigger write-through
    state.persist.assert_called_once()


def test_finish_tools_writes_through(mock_store):
    """Test finish_tools triggers immediate persistence."""
    state = AgentState("test query")
    state.store = mock_store

    state.persist = Mock()

    results = [{"name": "search", "result": "data", "success": True}]
    state.execution.finish_tools(results)

    # Should trigger write-through
    state.persist.assert_called_once()


def test_persist_serializes_complete_state():
    """Test persist() serializes execution + reasoning state."""
    state = AgentState("test query", user_id="user123")
    state.execution.add_message("user", "hello")
    state.reasoning.learn("insight")

    # Mock the store to capture serialized data
    state.store = Mock()
    state.store.save = Mock()

    state.persist()

    # Should call store.save with user_id and state data
    state.store.save.assert_called_once()
    call_args = state.store.save.call_args

    assert call_args[0][0] == "user123"  # user_id
    state_data = call_args[0][1]["state"]

    # Verify complete state serialization
    assert "execution" in state_data
    assert "reasoning" in state_data
    assert state_data["execution"]["query"] == "test query"
    assert len(state_data["execution"]["messages"]) == 1
    assert len(state_data["reasoning"]["insights"]) == 1


@pytest.mark.asyncio
async def test_persist_handles_async_gracefully():
    """Test persist() handles async/sync contexts gracefully."""
    state = AgentState("test query")

    # Should not raise exceptions
    state.persist()

    # Test in async context
    async def async_context():
        state.persist()

    await async_context()


def test_no_duplicate_insights():
    """Test reasoning.learn() prevents duplicate insights."""
    state = AgentState("test query")
    state.persist = Mock()  # Mock to count calls

    state.reasoning.learn("Same insight")
    state.reasoning.learn("Same insight")  # Duplicate
    state.reasoning.learn("Different insight")

    # Should only have 2 unique insights
    assert len(state.reasoning.insights) == 2
    assert "Same insight" in state.reasoning.insights
    assert "Different insight" in state.reasoning.insights

    # Should only persist unique additions
    assert state.persist.call_count == 2


def test_empty_insight_ignored():
    """Test reasoning.learn() ignores empty/whitespace insights."""
    state = AgentState("test query")
    state.persist = Mock()

    state.reasoning.learn("")
    state.reasoning.learn("   ")
    state.reasoning.learn("  \n\t  ")

    assert len(state.reasoning.insights) == 0
    state.persist.assert_not_called()
