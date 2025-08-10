"""Tests for state persistence across task lifecycles."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.state import State
from cogency.storage.state import StateStore


class MockStore(StateStore):
    """Mock store for testing."""

    def __init__(self):
        self.states = {}
        self.profiles = {}
        self.conversations = {}
        self.workspaces = {}
        self.process_id = "mock_process"

    # Mock store implementation
    async def save_user_profile(self, state_key: str, profile) -> bool:
        """Save user profile"""
        self.profiles[state_key] = profile
        return True

    async def load_user_profile(self, state_key: str):
        """Load user profile"""
        return self.profiles.get(state_key)

    async def delete_user_profile(self, state_key: str) -> bool:
        """Delete user profile"""
        if state_key in self.profiles:
            del self.profiles[state_key]
            return True
        return False

    # Conversation operations
    async def save_conversation(self, conversation) -> bool:
        """Save conversation"""
        self.conversations[conversation.conversation_id] = conversation
        return True

    async def load_conversation(self, conversation_id: str, user_id: str):
        """Load conversation"""
        return self.conversations.get(conversation_id)

    async def delete_conversation(self, conversation_id: str) -> bool:
        """Delete conversation"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]
            return True
        return False

    # Workspace operations
    async def save_task_workspace(self, task_id: str, user_id: str, workspace) -> bool:
        """Save task workspace"""
        key = f"{task_id}:{user_id}"
        self.workspaces[key] = workspace
        return True

    async def load_task_workspace(self, task_id: str, user_id: str):
        """Load task workspace"""
        key = f"{task_id}:{user_id}"
        return self.workspaces.get(key)

    async def delete_task_workspace(self, task_id: str) -> bool:
        """Delete task workspace"""
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
def mock_state_store(monkeypatch):
    """Replace SQLite with MockStore for testing."""
    mock = MockStore()

    def mock_sqlite(*args, **kwargs):
        return mock

    # Patch the exact import path used by State class
    monkeypatch.setattr("cogency.storage.state.SQLite", mock_sqlite)
    return mock


@pytest.fixture
def sample_state():
    from cogency.state.mutations import add_message

    state = State(query="test query", user_id="test_user")
    add_message(state, "user", "Hello")
    add_message(state, "assistant", "Hi there")
    return state


@pytest.mark.asyncio
async def test_start_task(mock_state_store):
    """Test State.start_task creates proper state structure."""
    state = await State.start_task("test query", "test_user")

    assert state.query == "test query"
    assert state.user_id == "test_user"
    assert state.task_id is not None

    # Verify state components exist
    assert state.profile is not None
    assert state.conversation is not None
    assert state.workspace is not None
    assert state.execution is not None

    # Verify workspace was saved to store
    workspace = await mock_state_store.load_task_workspace(state.task_id, "test_user")
    assert workspace is not None


@pytest.mark.asyncio
async def test_continue_task(mock_state_store):
    """Test State.continue_task loads existing workspace."""
    # First create a task
    original_state = await State.start_task("original query", "test_user")
    original_task_id = original_state.task_id

    # Modify the workspace
    original_state.workspace.objective = "modified objective"
    original_state.workspace.insights = ["test insight"]
    await mock_state_store.save_task_workspace(
        original_task_id, "test_user", original_state.workspace
    )

    # Make sure user profile exists (start_task would have created it)
    await mock_state_store.save_user_profile("test_user:default", original_state.profile)

    # Continue the task
    continued_state = await State.continue_task(original_task_id, "test_user")

    assert continued_state.task_id == original_task_id
    assert continued_state.workspace.objective == "modified objective"
    assert "test insight" in continued_state.workspace.insights

    # Execution should be fresh (Horizon 3 never persists)
    assert continued_state.execution.iteration == 0


@pytest.mark.asyncio
async def test_start_task_error(monkeypatch):
    """Test graceful degradation when storage fails during start_task."""
    failing_store = AsyncMock()
    failing_store.save_user_profile.side_effect = Exception("Save failed")
    failing_store.save_task_workspace.side_effect = Exception("Save failed")
    failing_store.load_user_profile.return_value = None

    def mock_sqlite(*args, **kwargs):
        return failing_store

    monkeypatch.setattr("cogency.storage.state.sqlite.SQLite", mock_sqlite)

    # Should handle errors gracefully (implementation dependent)
    try:
        state = await State.start_task("test query", "test_user")
        # If it succeeds, verify basic structure
        assert state.query == "test query"
    except Exception as e:
        # If it fails, it should be a controlled failure
        assert "Save failed" in str(e) or "Load failed" in str(e)


@pytest.mark.asyncio
async def test_continue_task_error(monkeypatch):
    """Test graceful degradation when load fails during continue_task."""
    failing_store = AsyncMock()
    failing_store.load_user_profile.side_effect = Exception("Load failed")
    failing_store.load_task_workspace.side_effect = Exception("Load failed")

    def mock_sqlite(*args, **kwargs):
        return failing_store

    monkeypatch.setattr("cogency.storage.state.sqlite.SQLite", mock_sqlite)

    # Should raise controlled exception for missing data
    with pytest.raises(Exception):
        await State.continue_task("fake-task-id", "test_user")


@pytest.mark.asyncio
async def test_three_horizon_persistence(mock_state_store):
    """Test complete Three-Horizon persistence model."""
    from cogency.state.mutations import learn_insight

    # Start a task
    state = await State.start_task("complex task", "test_user")

    # Set up user profile (Horizon 1)
    state.profile.preferences = {"style": "detailed"}
    state.profile.goals = ["Learn programming"]

    # Add complex execution state (Horizon 3)
    state.execution.iteration = 5
    state.execution.stop_reason = "depth"
    state.execution.response = "Final response"
    state.execution.pending_calls = [{"name": "test_tool", "args": {"arg": "value"}}]
    state.execution.completed_calls = [{"name": "previous_tool", "result": "success"}]

    # Add workspace data (Horizon 2) using mutations
    state.workspace.thoughts = [
        {"thinking": "Test thinking", "tool_calls": [{"name": "test_tool", "args": {}}]}
    ]
    learn_insight(state, "Important insight")

    # Save user profile manually (would be done by framework)
    await mock_state_store.save_user_profile("test_user:default", state.profile)
    await mock_state_store.save_task_workspace(state.task_id, "test_user", state.workspace)

    # Continue task (simulates loading from persistence)
    continued_state = await State.continue_task(state.task_id, "test_user")

    # Verify Horizon 1 (Profile) - PERSISTED
    assert continued_state.profile is not None
    assert continued_state.profile.preferences["style"] == "detailed"
    assert "Learn programming" in continued_state.profile.goals

    # Verify Horizon 2 (Workspace) - PERSISTED by task_id
    assert "Important insight" in continued_state.workspace.insights
    assert len(continued_state.workspace.thoughts) > 0

    # Verify Horizon 3 (Execution) - NOT PERSISTED (always fresh runtime state)
    assert continued_state.execution.iteration == 0  # Fresh execution state
    assert continued_state.execution.stop_reason is None  # Fresh execution state
    assert len(continued_state.execution.pending_calls) == 0  # Fresh execution state
