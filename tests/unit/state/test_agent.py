"""Unit tests for state persistence."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.state import State
from cogency.storage import Store
from cogency.storage.state import Persistence


class MockStore(Store):
    """Mock store for testing."""

    def __init__(self):
        self.states = {}
        self.profiles = {}
        self.workspaces = {}
        self.process_id = "mock_process"

    # CANONICAL Three-Horizon Store implementation
    async def save_user_profile(self, state_key: str, profile) -> bool:
        """Save Horizon 1 - UserProfile"""
        self.profiles[state_key] = profile
        return True

    async def load_user_profile(self, state_key: str):
        """Load Horizon 1 - UserProfile"""
        return self.profiles.get(state_key)

    async def delete_user_profile(self, state_key: str) -> bool:
        """Delete user profile"""
        if state_key in self.profiles:
            del self.profiles[state_key]
            return True
        return False

    async def save_task_workspace(self, task_id: str, user_id: str, workspace) -> bool:
        """Save Horizon 2 - Workspace"""
        key = f"{task_id}:{user_id}"
        self.workspaces[key] = workspace
        return True

    async def load_task_workspace(self, task_id: str, user_id: str):
        """Load Horizon 2 - Workspace"""
        key = f"{task_id}:{user_id}"
        return self.workspaces.get(key)

    async def delete_task_workspace(self, task_id: str) -> bool:
        """Delete Horizon 2 - Workspace"""
        keys_to_delete = [k for k in self.workspaces if k.startswith(f"{task_id}:")]
        for key in keys_to_delete:
            del self.workspaces[key]
        return len(keys_to_delete) > 0

    async def list_user_workspaces(self, user_id: str):
        """List all task_ids for user's active workspaces"""
        return [k.split(":")[0] for k in self.workspaces if k.endswith(f":{user_id}")]

    # LEGACY compatibility methods
    async def save(self, state_key: str, state: State) -> bool:
        from dataclasses import asdict

        # Use Three-Horizon model - no serialize_profile needed
        state_data = {
            "execution": asdict(state.execution),
            "reasoning": asdict(state.workspace),  # workspace is the new reasoning
            "user_profile": asdict(state.profile) if state.profile else None,
        }
        self.states[state_key] = {"state": state_data}
        return True

    async def load(self, state_key: str) -> dict:
        # Check for data saved via new canonical methods
        if state_key not in self.states:
            # Try to reconstruct from Three-Horizon data
            user_id = state_key.split(":")[0]
            profile = self.profiles.get(state_key)
            if profile:
                from dataclasses import asdict

                # Create compatible data structure
                state_data = {
                    "execution": {"query": "", "user_id": user_id},
                    "reasoning": {},
                    "user_profile": asdict(profile),
                }
                return {"state": state_data}

        return self.states.get(state_key)

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
    return Persistence(store=mock_store)


@pytest.fixture
def sample_state():
    from cogency.state.mutations import add_message

    state = State(query="test query", user_id="test_user")
    add_message(state, "user", "Hello")
    add_message(state, "assistant", "Hi there")
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
    persistence = Persistence(store=mock_store, enabled=False)
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
    # Create store that always fails on canonical methods
    failing_store = AsyncMock()
    failing_store.save_user_profile.side_effect = Exception("Save failed")
    failing_store.save_task_workspace.side_effect = Exception("Save failed")

    persistence = Persistence(store=failing_store)

    # Should not raise exception, just return False
    success = await persistence.save(sample_state)
    assert success is False


@pytest.mark.asyncio
async def test_load_error():
    """Test graceful degradation when load fails."""
    # Create store that always fails on canonical methods
    failing_store = AsyncMock()
    failing_store.load_user_profile.side_effect = Exception("Load failed")

    persistence = Persistence(store=failing_store)

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
    """Test complete state reconstruction with Three-Horizon structure."""
    from cogency.state.mutations import learn_insight

    # Use Three-Horizon model instead of old v1.0.0 API

    # Set up user profile (Horizon 1)
    sample_state.profile.preferences = {"style": "detailed"}
    sample_state.profile.goals = ["Learn programming"]

    # Add complex execution state (Horizon 3)
    sample_state.execution.iteration = 5
    sample_state.execution.stop_reason = "depth"
    sample_state.execution.response = "Final response"
    sample_state.execution.pending_calls = [{"name": "test_tool", "args": {"arg": "value"}}]
    sample_state.execution.completed_calls = [{"name": "previous_tool", "result": "success"}]

    # Add workspace data (Horizon 2) using mutations
    sample_state.workspace.thoughts = [
        {"thinking": "Test thinking", "tool_calls": [{"name": "test_tool", "args": {}}]}
    ]
    learn_insight(sample_state, "Important insight")

    # Save and load
    await persistence.save(sample_state)
    loaded_state = await persistence.load("test_user")

    # Verify Horizon 1 (UserProfile) - PERSISTED
    assert loaded_state.profile is not None
    assert loaded_state.profile.preferences["style"] == "detailed"
    assert "Learn programming" in loaded_state.profile.goals

    # Verify Horizon 3 (ExecutionState) - NOT PERSISTED (always fresh runtime state)
    # ExecutionState should be fresh/default since it's never persisted in Three-Horizon model
    assert loaded_state.execution.iteration == 0  # Fresh execution state
    assert loaded_state.execution.stop_reason is None  # Fresh execution state

    # Verify Horizon 2 (Workspace) - would be loaded by task continuation, not user load
    # The current load() method only loads UserProfile, not Workspace
    # Workspace loading requires task_id and is handled separately
