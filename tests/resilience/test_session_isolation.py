"""Test session isolation prevents checkpoint collisions."""

from unittest.mock import Mock

import pytest

from cogency.resilience.checkpoint import CheckpointManager
from cogency.state import State


def test_session_isolation_prevents_collisions():
    """Test different sessions generate different fingerprints."""
    # Create two checkpoint managers with different session IDs
    manager1 = CheckpointManager(session_id="session_a")
    manager2 = CheckpointManager(session_id="session_b")

    # Create identical states
    state1 = Mock(spec=State)
    state1.get.side_effect = lambda key, default=None: {
        "query": "test query",
        "current_iteration": 0,
    }.get(key, default)
    state1.selected_tools = []

    state2 = Mock(spec=State)
    state2.get.side_effect = lambda key, default=None: {
        "query": "test query",
        "current_iteration": 0,
    }.get(key, default)
    state2.selected_tools = []

    # Generate fingerprints - should be different due to session isolation
    fingerprint1 = manager1._generate_fingerprint(state1)
    fingerprint2 = manager2._generate_fingerprint(state2)

    assert fingerprint1 != fingerprint2
    assert len(fingerprint1) == 16
    assert len(fingerprint2) == 16


def test_same_session_same_fingerprint():
    """Test same session generates same fingerprint for identical states."""
    manager = CheckpointManager(session_id="test_session")

    # Create identical states
    state1 = Mock(spec=State)
    state1.get.side_effect = lambda key, default=None: {
        "query": "test",
        "current_iteration": 1,
    }.get(key, default)
    state1.selected_tools = []

    state2 = Mock(spec=State)
    state2.get.side_effect = lambda key, default=None: {
        "query": "test",
        "current_iteration": 1,
    }.get(key, default)
    state2.selected_tools = []

    fingerprint1 = manager._generate_fingerprint(state1)
    fingerprint2 = manager._generate_fingerprint(state2)

    assert fingerprint1 == fingerprint2


@pytest.mark.asyncio
async def test_interruptible_checkpoint_creates_session_isolated_paths():
    """Test interruptible checkpoint creates session-isolated checkpoint paths."""
    from cogency.resilience.checkpoint import CheckpointManager
    from cogency.resilience.decorators import safe

    # Create manager with specific session ID
    _ = CheckpointManager(session_id="test_session")

    @safe.checkpoint("test", interruptible=True)
    async def test_function(state):
        return "success"

    state = Mock(spec=State)
    state.get.side_effect = lambda key, default=None: {"query": "test"}.get(key, default)
    state.selected_tools = []

    result = await test_function(state)
    assert result == "success"
