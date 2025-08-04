"""Simple integration test for state persistence functionality."""

import tempfile
from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.config import PersistConfig
from cogency.persist import Filesystem
from cogency.persist.state import StatePersistence
from cogency.state import AgentState


@pytest.mark.asyncio
async def test_agent_setup():
    """Test that Agent properly sets up persistence components."""
    from cogency import Agent
    from cogency.config import PersistConfig

    with tempfile.TemporaryDirectory() as temp_dir:
        store = Filesystem(base_dir=temp_dir)

        # Test persistence enabled
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            persist_config = PersistConfig(enabled=True, store=store)
            agent = Agent("test_agent", tools=[], persist=persist_config)
            executor = await agent._get_executor()

        assert executor.config.persist is not None
        assert isinstance(executor.config.persist, PersistConfig)
        assert executor.config.persist.store is store
        assert executor.config.persist.enabled is True

        # Test persistence disabled
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            agent = Agent("test_agent", tools=[])
            executor = await agent._get_executor()

        # Default persistence config should be None when disabled
        assert executor.config.persist is None or executor.config.persist.enabled is False


@pytest.mark.asyncio
async def test_get_state():
    """Test the get_state utility function directly."""

    from cogency.persist.utils import _get_state

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
    assert state.execution.user_id == "test_user"
    assert state.execution.query == "test query"
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
    assert state2.execution.query == "new query"  # Query updated


@pytest.mark.asyncio
async def test_end_to_end():
    """Test complete state persistence flow with v1.0.0 structure."""

    with tempfile.TemporaryDirectory() as temp_dir:
        store = Filesystem(base_dir=temp_dir)
        manager = StatePersistence(store=store)

        # Create and save state with v1.0.0 structure
        from cogency.state.user import UserProfile

        profile = UserProfile(user_id="test_user")
        profile.preferences = {"language": "Python"}
        profile.communication_style = "concise"

        state = AgentState(query="test query", user_id="test_user", user_profile=profile)
        state.execution.add_message("user", "Hello")
        state.execution.iteration = 2
        state.reasoning.add_insight("Test insight")
        state.execution.add_message("assistant", "Hi there")
        state.execution.iteration = 3

        success = await manager.save(state)
        assert success is True

        # Load state back
        loaded_state = await manager.load("test_user")

        assert loaded_state is not None
        assert loaded_state.execution.user_id == "test_user"
        assert loaded_state.execution.query == "test query"
        assert loaded_state.execution.iteration == 3
        assert len(loaded_state.execution.messages) == 2
        assert loaded_state.execution.messages[0]["content"] == "Hello"
        assert loaded_state.execution.messages[1]["content"] == "Hi there"

        # Test v1.0.0 specific features
        assert loaded_state.user is not None
        assert loaded_state.user.user_id == "test_user"
        assert loaded_state.user.preferences["language"] == "Python"
        assert loaded_state.user.communication_style == "concise"
        assert "Test insight" in loaded_state.reasoning.insights
