"""Simple integration test for state persistence functionality."""

import tempfile
from unittest.mock import patch

import pytest

from cogency.agent import Agent
from cogency.persistence import FileBackend, StateManager
from cogency.state import State


@pytest.mark.asyncio
async def test_persistence_setup_in_agent():
    """Test that Agent properly sets up persistence components."""

    with tempfile.TemporaryDirectory() as temp_dir:
        backend = FileBackend(base_dir=temp_dir)

        # Test persistence enabled
        agent = Agent(name="test_agent", persistence=backend)

        from cogency.decorators import get_config

        config = get_config()
        assert config["persistence"] is not None
        assert isinstance(config["persistence"], StateManager)
        assert config["persistence"].backend is backend
        assert config["persistence"].enabled is True

        # Test persistence disabled
        agent_disabled = Agent(name="test_agent", persistence=None)

        from cogency.decorators import get_config

        config = get_config()
        assert config["persistence"] is None


@pytest.mark.asyncio
async def test_get_state_utility():
    """Test the get_state utility function directly."""

    from cogency.persistence.utils import get_state

    user_states = {}

    # Test creating new state
    state = await get_state(
        user_id="test_user",
        query="test query",
        depth=10,
        user_states=user_states,
        persistence_manager=None,
        llm=None,
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
        persistence_manager=None,
        llm=None,
    )

    assert state2 is state  # Should be same object
    assert state2.query == "new query"  # Query updated


@pytest.mark.asyncio
async def test_state_persistence_end_to_end():
    """Test complete state persistence flow without full agent execution."""

    with tempfile.TemporaryDirectory() as temp_dir:
        backend = FileBackend(base_dir=temp_dir)
        manager = StateManager(backend=backend)

        # Create and save state
        state = State(query="test query", user_id="test_user")
        state.add_message("user", "Hello")
        state.add_message("assistant", "Hi there")
        state.iteration = 3

        success = await manager.save_state(
            state, llm_provider="test_provider", llm_model="test_model", tools_count=2
        )
        assert success is True

        # Load state back
        loaded_state = await manager.load_state(
            "test_user",
            validate_llm=True,
            expected_llm_provider="test_provider",
            expected_llm_model="test_model",
        )

        assert loaded_state is not None
        assert loaded_state.user_id == "test_user"
        assert loaded_state.query == "test query"
        assert loaded_state.iteration == 3
        assert len(loaded_state.messages) == 2
        assert loaded_state.messages[0]["content"] == "Hello"
        assert loaded_state.messages[1]["content"] == "Hi there"
