"""Simple integration test for state persistence functionality."""

import tempfile
from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.config import PersistConfig
from cogency.state import State
from cogency.storage import SQLite
from cogency.storage.state import Persistence


@pytest.mark.asyncio
async def test_agent_setup():
    """Test that Agent properly sets up persistence components."""
    from cogency import Agent
    from cogency.config import PersistConfig

    with tempfile.TemporaryDirectory() as temp_dir:
        store = SQLite(db_path=f"{temp_dir}/test.db")

        # Test persistence enabled
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            persist_config = PersistConfig(enabled=True, store=store)
            agent = Agent("test_agent", tools=[], persist=persist_config)
            await agent._get_executor()

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            agent = Agent("test_agent", tools=[])
            await agent._get_executor()


@pytest.mark.asyncio
async def test_get_state():
    """Test the get_state utility function directly."""

    from cogency.storage.utils import _get_state

    user_states = {}

    # Test creating new state
    state = await _get_state(
        user_id="test_user",
        query="test query",
        max_iterations=10,
        user_states=user_states,
        persistence=None,
    )

    assert state is not None
    assert state.user_id == "test_user"
    assert state.query == "test query"
    assert "test_user" in user_states

    # Test getting existing state
    state2 = await _get_state(
        user_id="test_user",
        query="new query",
        max_iterations=10,
        user_states=user_states,
        persistence=None,
    )

    assert state2 is state  # Should be same object
    assert state2.query == "new query"  # Query updated


@pytest.mark.asyncio
async def test_end_to_end():
    """Test complete state persistence flow with v1.0.0 structure."""

    with tempfile.TemporaryDirectory() as temp_dir:
        store = SQLite(db_path=f"{temp_dir}/test.db")
        manager = Persistence(store=store)

        # Create and save state with v1.0.0 structure
        from cogency.state.agent import UserProfile

        profile = UserProfile(user_id="test_user")
        profile.preferences = {"language": "Python"}
        profile.communication_style = "concise"

        from cogency.state.mutations import add_message, learn_insight

        state = State(query="test query", user_id="test_user")
        state.profile = profile
        add_message(state, "user", "Hello")
        state.execution.iteration = 2
        learn_insight(state, "Test insight")
        add_message(state, "assistant", "Hi there")
        state.execution.iteration = 3

        success = await manager.save(state)
        assert success is True

        # Load state back
        loaded_state = await manager.load("test_user")

        assert loaded_state is not None
        assert loaded_state.user_id == "test_user"
        # Query is NOT persisted in Three-Horizon model (ExecutionState is runtime-only)
        # Only UserProfile (Horizon 1) is persisted in basic user load
        assert loaded_state.query == ""  # Fresh state
        assert loaded_state.execution.iteration == 0  # Fresh ExecutionState
        # Messages are part of ExecutionState - NOT persisted in Three-Horizon model
        assert len(loaded_state.execution.messages) == 0  # Fresh ExecutionState

        # Test Three-Horizon UserProfile persistence (Horizon 1)
        assert loaded_state.profile is not None
        assert loaded_state.profile.user_id == "test_user"
        assert loaded_state.profile.preferences["language"] == "Python"
        assert loaded_state.profile.communication_style == "concise"
        # Workspace insights would only be available if we loaded by task_id
        # Basic user load only restores UserProfile (Horizon 1)
