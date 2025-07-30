"""Simple integration test for state persistence functionality."""

import tempfile
from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.config import PersistConfig
from cogency.persist import Filesystem, StatePersistence
from cogency.state import State


@pytest.mark.asyncio
async def test_agent_setup():
    """Test that Agent properly sets up persistence components."""

    with tempfile.TemporaryDirectory() as temp_dir:
        store = Filesystem(base_dir=temp_dir)

        # Test persistence enabled
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            Agent(name="test_agent", persist=store)

        from cogency.decorators import get_config

        config = get_config()
        assert config.persist is not None
        assert isinstance(config.persist, PersistConfig)
        assert config.persist.store is store
        assert config.persist.enabled is True

        # Test persistence disabled
        Agent(name="test_agent", persist=None)

        config = get_config()
        assert config.persist is None


@pytest.mark.asyncio
async def test_get_state():
    """Test the get_state utility function directly."""

    from cogency.persist.utils import get_state

    user_states = {}

    # Test creating new state
    state = await get_state(
        user_id="test_user",
        query="test query",
        depth=10,
        user_states=user_states,
        persistence=None,
    )

    assert state is not None
    assert state.user_id == "test_user"
    assert state.query == "test query"
    assert "test_user" in user_states

    # Test getting existing state
    state2 = await get_state(
        user_id="test_user",
        query="new query",
        depth=10,
        user_states=user_states,
        persistence=None,
    )

    assert state2 is state  # Should be same object
    assert state2.query == "new query"  # Query updated


@pytest.mark.asyncio
async def test_end_to_end():
    """Test complete state persistence flow without full agent execution."""

    with tempfile.TemporaryDirectory() as temp_dir:
        store = Filesystem(base_dir=temp_dir)
        manager = StatePersistence(store=store)

        # Create and save state
        state = State(query="test query", user_id="test_user")
        state.add_message("user", "Hello")
        state.add_message("assistant", "Hi there")
        state.iteration = 3

        success = await manager.save(state)
        assert success is True

        # Load state back
        loaded_state = await manager.load("test_user")

        assert loaded_state is not None
        assert loaded_state.user_id == "test_user"
        assert loaded_state.query == "test query"
        assert loaded_state.iteration == 3
        assert len(loaded_state.messages) == 2
        assert loaded_state.messages[0]["content"] == "Hello"
        assert loaded_state.messages[1]["content"] == "Hi there"
