"""Test memory synthesis step functionality."""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock

import pytest

from cogency.state import AgentState, ExecutionState, UserProfile
from cogency.steps.synthesize.core import (
    _check_high_value_interaction,
    _check_session_end,
    _check_threshold,
    _should_synthesize,
    synthesize,
)


class MockMemory:
    """Mock memory service for testing."""

    def __init__(self):
        self.update_impression = AsyncMock()
        self._load_profile = AsyncMock()
        self.user_profile = UserProfile(user_id="test_user")

    async def _load_profile(self, user_id: str):
        return self.user_profile


@pytest.fixture
def mock_memory():
    return MockMemory()


@pytest.fixture
def agent_state():
    state = AgentState(query="test query", user_id="test_user")
    state.execution.user_id = "test_user"
    state.execution.iteration = 1
    return state


@pytest.fixture
def user_profile():
    profile = UserProfile(user_id="test_user")
    profile.interaction_count = 5
    profile.synthesis_threshold = 5
    profile.last_synthesis_count = 0
    profile.last_interaction_time = datetime.now() - timedelta(minutes=10)
    profile.session_timeout = 1800  # 30 minutes
    return profile


@pytest.mark.asyncio
async def test_synthesize_no_memory(agent_state):
    """Test synthesis with no memory service."""
    await synthesize(agent_state, memory=None)
    # Should complete without error


@pytest.mark.asyncio
async def test_synthesize_with_triggers(agent_state, mock_memory, user_profile):
    """Test synthesis when triggers are met."""
    agent_state.user_profile = user_profile

    # Set up threshold trigger
    user_profile.interaction_count = 10
    user_profile.last_synthesis_count = 0

    await synthesize(agent_state, mock_memory)

    # Should call synthesis
    mock_memory.update_impression.assert_called_once()


@pytest.mark.asyncio
async def test_synthesize_no_triggers(agent_state, mock_memory, user_profile):
    """Test synthesis when no triggers are met."""
    agent_state.user_profile = user_profile

    # No triggers met
    user_profile.interaction_count = 2
    user_profile.last_synthesis_count = 0
    user_profile.synthesis_threshold = 5
    user_profile.last_interaction_time = datetime.now() - timedelta(minutes=5)

    await synthesize(agent_state, mock_memory)

    # Should not call synthesis
    mock_memory.update_impression.assert_not_called()


@pytest.mark.asyncio
async def test_synthesize_idempotence(agent_state, mock_memory, user_profile):
    """Test that synthesis doesn't run twice concurrently."""
    agent_state.user_profile = user_profile

    # Set up triggers
    user_profile.interaction_count = 10
    user_profile.last_synthesis_count = 0

    # Mark synthesis in progress
    user_profile._synthesis_lock = True

    await synthesize(agent_state, mock_memory)

    # Should not call synthesis due to lock
    mock_memory.update_impression.assert_not_called()


def test_check_threshold_triggered(user_profile):
    """Test threshold trigger logic."""
    user_profile.interaction_count = 10
    user_profile.last_synthesis_count = 0
    user_profile.synthesis_threshold = 5

    assert _check_threshold(user_profile) is True


def test_check_threshold_not_triggered(user_profile):
    """Test threshold not triggered."""
    user_profile.interaction_count = 3
    user_profile.last_synthesis_count = 0
    user_profile.synthesis_threshold = 5

    assert _check_threshold(user_profile) is False


def test_check_session_end_triggered(user_profile, agent_state):
    """Test session end detection."""
    # Set time 45 minutes ago (longer than 30min timeout)
    user_profile.last_interaction_time = datetime.now() - timedelta(minutes=45)
    user_profile.session_timeout = 1800  # 30 minutes

    assert _check_session_end(user_profile, agent_state) is True


def test_check_session_end_not_triggered(user_profile, agent_state):
    """Test session end not triggered."""
    # Set time 10 minutes ago (within 30min timeout)
    user_profile.last_interaction_time = datetime.now() - timedelta(minutes=10)
    user_profile.session_timeout = 1800  # 30 minutes

    assert _check_session_end(user_profile, agent_state) is False


def test_check_high_value_interaction_high_iterations(agent_state):
    """Test high value detection with high iterations."""
    agent_state.execution.iteration = 5

    assert _check_high_value_interaction(agent_state) is True


def test_check_high_value_interaction_multiple_tools(agent_state):
    """Test high value detection with multiple tools."""
    agent_state.execution.iteration = 1
    agent_state.execution.completed_calls = [
        {"tool": "search"},
        {"tool": "http"},
        {"tool": "files"},
    ]

    assert _check_high_value_interaction(agent_state) is True


def test_check_high_value_interaction_not_triggered(agent_state):
    """Test high value not triggered."""
    agent_state.execution.iteration = 1
    agent_state.execution.completed_calls = [{"tool": "search"}]

    assert _check_high_value_interaction(agent_state) is False


def test_should_synthesize_threshold(user_profile, agent_state):
    """Test synthesis trigger with threshold."""
    user_profile.interaction_count = 10
    user_profile.last_synthesis_count = 0
    user_profile.synthesis_threshold = 5
    user_profile.last_interaction_time = datetime.now() - timedelta(minutes=5)
    agent_state.execution.iteration = 1

    assert _should_synthesize(user_profile, agent_state) is True


def test_should_synthesize_session_end(user_profile, agent_state):
    """Test synthesis trigger with session end."""
    user_profile.interaction_count = 2
    user_profile.last_synthesis_count = 0
    user_profile.synthesis_threshold = 5
    user_profile.last_interaction_time = datetime.now() - timedelta(minutes=45)
    user_profile.session_timeout = 1800
    agent_state.execution.iteration = 1

    assert _should_synthesize(user_profile, agent_state) is True


def test_should_synthesize_high_value(user_profile, agent_state):
    """Test synthesis trigger with high value interaction."""
    user_profile.interaction_count = 2
    user_profile.last_synthesis_count = 0
    user_profile.synthesis_threshold = 5
    user_profile.last_interaction_time = datetime.now() - timedelta(minutes=5)
    agent_state.execution.iteration = 5  # High value

    assert _should_synthesize(user_profile, agent_state) is True


def test_should_synthesize_no_triggers(user_profile, agent_state):
    """Test synthesis not triggered when no conditions met."""
    user_profile.interaction_count = 2
    user_profile.last_synthesis_count = 0
    user_profile.synthesis_threshold = 5
    user_profile.last_interaction_time = datetime.now() - timedelta(minutes=5)
    agent_state.execution.iteration = 1

    assert _should_synthesize(user_profile, agent_state) is False


def test_should_synthesize_no_profile(agent_state):
    """Test synthesis with no user profile."""
    assert _should_synthesize(None, agent_state) is False
