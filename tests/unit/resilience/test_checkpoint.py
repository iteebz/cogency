"""Critical checkpoint tests - basic save/restore, corruption, recovery context."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from cogency.context import Context
from cogency.resilience.checkpoint import CheckpointManager, resume
from cogency.state import State


@pytest.fixture
def checkpoint_manager(tmp_path):
    return CheckpointManager(checkpoint_dir=tmp_path)


@pytest.fixture
def test_state():
    context = Context(query="test query", messages=[{"role": "user", "content": "test"}])
    state = State(context=context, query="test query")
    state.flow["selected_tools"] = []
    state.flow["iteration"] = 1
    return state


def test_roundtrip(checkpoint_manager, test_state):
    # Save checkpoint
    checkpoint_id = checkpoint_manager.save_checkpoint(test_state)
    assert checkpoint_id

    # Verify file exists
    checkpoint_path = checkpoint_manager._get_checkpoint_path(checkpoint_id)
    assert checkpoint_path.exists()

    # Load checkpoint
    checkpoint_data = checkpoint_manager.load_checkpoint(checkpoint_id)
    assert checkpoint_data
    assert checkpoint_data["query"] == "test query"
    assert checkpoint_data["iteration"] == 1
    assert checkpoint_data["fingerprint"] == checkpoint_id


def test_corruption(checkpoint_manager, test_state):
    # Save valid checkpoint first
    checkpoint_id = checkpoint_manager.save_checkpoint(test_state)
    checkpoint_path = checkpoint_manager._get_checkpoint_path(checkpoint_id)

    # Corrupt the JSON file
    with checkpoint_path.open("w") as f:
        f.write('{"invalid": json}')

    # Finding checkpoint should fail and clean up corrupted file
    found_id = checkpoint_manager.find_checkpoint(test_state)
    assert found_id is None
    assert not checkpoint_path.exists()


def test_recovery_message(checkpoint_manager, test_state):
    # Add some tool execution history
    test_state.flow["prev_tool_calls"] = [
        {"name": "search", "args": {"query": "test"}},
        {"name": "read", "args": {"file": "test.py"}},
    ]
    test_state.flow["iteration"] = 3

    # Save checkpoint
    checkpoint_id = checkpoint_manager.save_checkpoint(test_state, "act")

    # Mock checkpoints to use our test manager
    with patch("cogency.resilience.checkpoint.checkpoints", checkpoint_manager):
        # Resume from checkpoint
        success = resume(test_state)
        assert success

        # Verify recovery context was added
        assert test_state.flow["resume_from_checkpoint"] is True
        assert test_state.flow["checkpoint_id"] == checkpoint_id

        # Check recovery message was injected into context
        messages = test_state.context.chat
        recovery_msg = next((msg for msg in messages if msg["role"] == "system"), None)
        assert recovery_msg
        assert "RESUMING FROM CHECKPOINT" in recovery_msg["content"]
        assert "Previously completed tools: search, read" in recovery_msg["content"]
        assert "Continue from iteration 3" in recovery_msg["content"]
