"""Unit tests for state persistence."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.persist import StatePersistence, Store
from cogency.state import AgentState


class MockStore(Store):
    """Mock store for testing."""

    def __init__(self):
        self.states = {}
        self.process_id = "mock_process"

    async def save(self, state_key: str, state: AgentState) -> bool:
        self.states[state_key] = {"state": state}
        return True

    async def load(self, state_key: str) -> dict:
        data = self.states.get(state_key)
        if data:
            # Convert State object back to dict format expected by persistence
            return {
                "state": (
                    data["state"].__dict__ if hasattr(data["state"], "__dict__") else data["state"]
                ),
            }
        return None

    async def delete(self, state_key: str) -> bool:
        if state_key in self.states:
            del self.states[state_key]
            return True
        return False

    async def list_states(self, user_id: str) -> list:
        return [k for k in self.states if k.startswith(user_id)]


@pytest.fixture
def mock_store():
    return MockStore()


@pytest.fixture
def persistence(mock_store):
    return StatePersistence(store=mock_store)


@pytest.fixture
def sample_state():
    state = AgentState(query="test query", user_id="test_user")
    state.execution.add_message("user", "Hello")
    state.execution.add_message("assistant", "Hi there")
    return state


@pytest.mark.asyncio
async def test_save(persistence, sample_state):
    """Test basic saving state functionality."""
    success = await persistence.save(sample_state)

    assert success is True

    # Verify state was saved
    state_key = persistence._state_key("test_user")
    stored_data = await persistence.store.load(state_key)

    assert stored_data is not None


@pytest.mark.asyncio
async def test_disabled(mock_store):
    """Test persistence with persistence disabled."""
    persistence = StatePersistence(store=mock_store, enabled=False)
    sample_state = AgentState(query="test", user_id="test_user")

    # Save should succeed silently
    success = await persistence.save(sample_state)
    assert success is True

    # But nothing should be actually saved
    assert len(mock_store.states) == 0

    # Load should return None
    loaded_state = await persistence.load("test_user")
    assert loaded_state is None


@pytest.mark.asyncio
async def test_save_error(sample_state):
    """Test graceful degradation when save fails."""
    # Create store that always fails
    failing_store = AsyncMock()
    failing_store.save.side_effect = Exception("Save failed")

    persistence = StatePersistence(store=failing_store)

    # Should not raise exception, just return False
    success = await persistence.save(sample_state)
    assert success is False


@pytest.mark.asyncio
async def test_load_error():
    """Test graceful degradation when load fails."""
    # Create store that always fails
    failing_store = AsyncMock()
    failing_store.load.side_effect = Exception("Load failed")

    persistence = StatePersistence(store=failing_store)

    # Should not raise exception, just return None
    loaded_state = await persistence.load("test_user")
    assert loaded_state is None


@pytest.mark.asyncio
async def test_key_gen(persistence, sample_state):
    """Test state key generation."""
    success = await persistence.save(sample_state)

    assert success is True

    # Check state key was generated correctly
    state_key = persistence._state_key("test_user")
    assert state_key.startswith("test_user:")

    stored_data = await persistence.store.load(state_key)
    assert stored_data is not None


@pytest.mark.asyncio
async def test_reconstruct(persistence, sample_state):
    """Test complete state reconstruction with v1.0.0 structure."""
    # Add complex v1.0.0 state data
    from cogency.state.memory import UserProfile

    # Set up user profile
    profile = UserProfile(user_id="test_user")
    profile.preferences = {"style": "detailed"}
    profile.goals = ["Learn programming"]
    sample_state.user_profile = profile

    # Add complex execution state
    sample_state.execution.iteration = 5
    sample_state.execution.stop_reason = "depth"
    sample_state.execution.response = "Final response"
    sample_state.execution.pending_calls = [{"name": "test_tool", "args": {"param": "value"}}]
    sample_state.execution.completed_calls = [{"name": "previous_tool", "result": "success"}]

    # Record thinking in reasoning context
    sample_state.reasoning.record_thinking("Test thinking", [{"name": "test_tool", "args": {}}])
    sample_state.reasoning.add_insight("Important insight")

    # Save and load
    await persistence.save(sample_state)
    loaded_state = await persistence.load("test_user")

    # Verify all v1.0.0 fields reconstructed correctly
    assert loaded_state.execution.iteration == 5
    assert loaded_state.execution.stop_reason == "depth"
    assert loaded_state.execution.response == "Final response"
    assert loaded_state.execution.pending_calls == [
        {"name": "test_tool", "args": {"param": "value"}}
    ]
    assert loaded_state.execution.completed_calls == [
        {"name": "previous_tool", "result": "success"}
    ]

    # Verify reasoning state
    # Thoughts are stored as dicts with metadata, not plain strings
    thought_contents = [thought.get("thinking", "") for thought in loaded_state.reasoning.thoughts]
    assert "Test thinking" in thought_contents
    assert "Important insight" in loaded_state.reasoning.insights

    # Verify user profile
    assert loaded_state.user_profile is not None
    assert loaded_state.user_profile.preferences["style"] == "detailed"
    assert "Learn programming" in loaded_state.user_profile.goals
