"""Unit tests for state persistence."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.persist import StatePersistence, Store
from cogency.state import State


class MockStore(Store):
    """Mock store for testing."""

    def __init__(self):
        self.states = {}
        self.process_id = "mock_process"

    async def save(self, state_key: str, state: State) -> bool:
        self.states[state_key] = {"state": state, "schema_version": "1.0"}
        return True

    async def load(self, state_key: str) -> dict:
        data = self.states.get(state_key)
        if data:
            # Convert State object back to dict format expected by persistence
            return {
                "state": data["state"].__dict__
                if hasattr(data["state"], "__dict__")
                else data["state"],
                "schema_version": data["schema_version"],
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
    state = State(query="test query", user_id="test_user")
    state.add_message("user", "Hello")
    state.add_message("assistant", "Hi there")
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
    assert stored_data["schema_version"] == "1.0"


@pytest.mark.asyncio
async def test_disabled(mock_store):
    """Test persistence with persistence disabled."""
    persistence = StatePersistence(store=mock_store, enabled=False)
    sample_state = State(query="test", user_id="test_user")

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
    """Test complete state reconstruction."""
    # Add more complex state data
    sample_state.iteration = 5
    sample_state.stop_reason = "depth"
    sample_state.response = "Final response"
    sample_state.add_action(
        mode="fast",
        thinking="Test thinking",
        planning="Test planning",
        reflection="Test reflection",
        approach="direct",
        tool_calls=[{"name": "test_tool", "args": {}}],
    )

    # Save and load
    await persistence.save(sample_state)
    loaded_state = await persistence.load("test_user")

    # Verify all fields reconstructed correctly
    assert loaded_state.iteration == 5
    assert loaded_state.stop_reason == "depth"
    assert loaded_state.response == "Final response"
    assert len(loaded_state.actions) == 1
    assert loaded_state.actions[0]["thinking"] == "Test thinking"
    assert loaded_state.callback is None  # Should not persist callbacks
