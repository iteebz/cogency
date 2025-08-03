"""Test checkpoint decorator and functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cogency.robust.checkpoint import Checkpoint, checkpoint, checkpointer
from cogency.state import AgentState


@pytest.fixture
def temp_checkpoint_dir():
    """Create temporary directory for checkpoint tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_state():
    """Create test state for checkpoint tests."""
    state = AgentState(query="test query", user_id="test_user")
    state.execution.iteration = 1
    return state


def test_init(temp_checkpoint_dir):
    """Test checkpoint initialization."""
    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)
    assert cp.checkpoint_dir == temp_checkpoint_dir
    assert cp.checkpoint_dir.exists()


def test_fingerprint(temp_checkpoint_dir, test_state):
    """Test fingerprint generation is deterministic."""
    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    fingerprint1 = cp._generate_fingerprint(test_state)
    fingerprint2 = cp._generate_fingerprint(test_state)

    assert fingerprint1 == fingerprint2
    assert len(fingerprint1) == 16  # SHA256 _truncated to 16 chars


def test_fingerprint_changes(temp_checkpoint_dir):
    """Test fingerprint changes when state changes."""
    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    state1 = AgentState(query="query1")
    state1.execution.iteration = 1
    state2 = AgentState(query="query2")
    state2.execution.iteration = 1

    fingerprint1 = cp._generate_fingerprint(state1)
    fingerprint2 = cp._generate_fingerprint(state2)

    assert fingerprint1 != fingerprint2


def test_save_load(temp_checkpoint_dir, test_state):
    """Test saving and loading checkpoint data."""
    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    # Save checkpoint
    fingerprint = cp.save(test_state, "test_type")

    # Load checkpoint
    checkpoint_data = cp.load(fingerprint)

    assert checkpoint_data is not None
    assert checkpoint_data["query"] == "test query"
    assert checkpoint_data["iteration"] == 1
    assert checkpoint_data["checkpoint_type"] == "test_type"


def test_find_existing(temp_checkpoint_dir, test_state):
    """Test finding existing checkpoint."""
    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    # Save checkpoint
    saved_fingerprint = cp.save(test_state, "test_type")

    # Find checkpoint
    found_fingerprint = cp.find(test_state)

    assert found_fingerprint == saved_fingerprint


def test_find_missing(temp_checkpoint_dir, test_state):
    """Test finding nonexistent checkpoint returns None."""
    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    # Don't save anything
    found_fingerprint = cp.find(test_state)

    assert found_fingerprint is None


def test_resume_missing(temp_checkpoint_dir):
    """Test resume returns False when no checkpoint exists."""
    from cogency.robust.checkpoint import resume

    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    with patch("cogency.robust.checkpoint.checkpointer", cp):
        state = AgentState(query="no checkpoint")
        state.execution.iteration = 1
        result = resume(state)
        assert result is False


def test_resume_valid(temp_checkpoint_dir):
    """Test resume successfully restores state from checkpoint."""
    from cogency.robust.checkpoint import resume

    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    # Create and save initial state
    original_state = AgentState(query="resume test")
    original_state.execution.iteration = 3
    original_state.execution.mode = "detailed"
    original_state.execution.pending_calls = [{"name": "test_tool", "args": {}}]
    original_state.execution.add_message("user", "original message")
    # Legacy properties no longer exist in v1.0.0

    cp.save(original_state, "test_resume")

    # Create new state with same fingerprint signature
    new_state = AgentState(query="resume test")
    new_state.execution.iteration = 3  # Must match for fingerprint to be same
    new_state.execution.mode = "fast"  # This will get overwritten by resume

    with patch("cogency.robust.checkpoint.checkpointer", cp):
        result = resume(new_state)

        assert result is True
        assert new_state.execution.iteration == 3
        assert new_state.execution.mode == "detailed"
        assert new_state.execution.pending_calls == [{"name": "test_tool", "args": {}}]
        # Legacy properties no longer exist in v1.0.0

        # Should have original message plus resume message
        assert len(new_state.execution.messages) == 2
        assert new_state.execution.messages[0]["content"] == "original message"
        assert "RESUMING FROM CHECKPOINT" in new_state.execution.messages[1]["content"]


def test_resume_corrupted(temp_checkpoint_dir):
    """Test resume handles corrupted checkpoint gracefully."""
    from cogency.robust.checkpoint import resume

    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    # Create state and save checkpoint
    state = AgentState(query="corrupt test")
    state.execution.iteration = 1
    fingerprint = cp.save(state, "corrupt_test")

    # Corrupt the checkpoint file
    checkpoint_path = cp._get_checkpoint_path(fingerprint)
    with checkpoint_path.open("w") as f:
        f.write("invalid json content")

    # Create new state for resume
    new_state = AgentState(query="corrupt test")
    new_state.execution.iteration = 1

    with patch("cogency.robust.checkpoint.checkpointer", cp):
        result = resume(new_state)

        # Should fail gracefully without exceptions
        assert result is False


@pytest.mark.asyncio
async def test_integration(temp_checkpoint_dir):
    """Integration test: save checkpoint and resume from it."""
    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    # Create initial state
    state = AgentState(query="integration test")
    state.execution.iteration = 2

    # Save checkpoint
    fingerprint = cp.save(state, "integration_test")
    assert fingerprint is not None

    # Create new state with same signature
    new_state = AgentState(query="integration test")
    new_state.execution.iteration = 2

    # Should find the checkpoint
    found_fingerprint = cp.find(new_state)
    assert found_fingerprint == fingerprint

    # Should load the checkpoint data
    checkpoint_data = cp.load(found_fingerprint)
    assert checkpoint_data["query"] == "integration test"
    assert checkpoint_data["iteration"] == 2
