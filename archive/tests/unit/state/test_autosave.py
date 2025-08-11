"""Tests for autosave persistence - Database as State."""

from unittest.mock import AsyncMock

import pytest

from cogency.state import State


@pytest.fixture
def mock_store():
    """Mock store for testing write-through behavior."""
    store = AsyncMock()
    store.save = AsyncMock(return_value=True)
    return store


def test_state_auto_creates_store():
    """Test State is properly initialized."""
    state = State("test query")

    assert state.query == "test query"
    assert state.execution is not None
    assert state.workspace is not None


def test_add_message_through(mock_store):
    """Test add_message works correctly with mutations."""
    from cogency.state.mutations import add_message

    state = State("test query")

    # Use proper mutation API
    add_message(state, "user", "hello")

    # Should add message to execution state
    assert len(state.execution.messages) == 1
    assert state.execution.messages[0]["content"] == "hello"


def test_learn_through(mock_store):
    """Test learn_insight works correctly with mutations."""
    from cogency.state.mutations import learn_insight

    state = State("test query")

    # Use proper mutation API
    learn_insight(state, "New insight")

    # Should add insight to workspace
    assert "New insight" in state.workspace.insights


def test_finish_tools_through(mock_store):
    """Test finish_tools works correctly with mutations."""
    from cogency.state.mutations import finish_tools

    state = State("test query")

    # Use proper mutation API
    results = [{"name": "search", "result": "data", "success": True}]
    finish_tools(state, results)

    # Should add results to completed calls
    assert len(state.execution.completed_calls) == 1
    assert state.execution.completed_calls[0]["name"] == "search"


def test_persist_complete_state():
    """Test Three-Horizon state structure."""
    from cogency.state.mutations import add_message, learn_insight

    state = State("test query", user_id="user123")
    add_message(state, "user", "hello")
    learn_insight(state, "insight")

    # Should have proper Three-Horizon structure
    assert state.query == "test query"
    assert state.user_id == "user123"
    assert len(state.execution.messages) == 1
    assert "insight" in state.workspace.insights


@pytest.mark.asyncio
async def test_persist_handles_async_gracefully():
    """Test mutations work in async context."""
    from cogency.state.mutations import add_message

    state = State("test query")

    # Test mutations work in async context
    async def async_context():
        add_message(state, "user", "async message")

    await async_context()

    assert len(state.execution.messages) == 1
    assert state.execution.messages[0]["content"] == "async message"


def test_no_duplicate_insights():
    """Test learn_insight prevents duplicate insights."""
    from cogency.state.mutations import learn_insight

    state = State("test query")

    learn_insight(state, "Same insight")
    learn_insight(state, "Same insight")  # Duplicate
    learn_insight(state, "Different insight")

    # Should only have 2 unique insights
    assert len(state.workspace.insights) == 2
    assert "Same insight" in state.workspace.insights
    assert "Different insight" in state.workspace.insights


def test_empty_insight_ignored():
    """Test learn_insight ignores empty/whitespace insights."""
    from cogency.state.mutations import learn_insight

    state = State("test query")

    learn_insight(state, "")
    learn_insight(state, "   ")
    learn_insight(state, "  \n\t  ")

    assert len(state.workspace.insights) == 0
