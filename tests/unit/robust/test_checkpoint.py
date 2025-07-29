"""Test checkpoint decorator and functionality."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from cogency.state import State
from cogency.robust.checkpoint import Checkpoint, checkpoint, checkpointer


@pytest.fixture
def temp_checkpoint_dir():
    """Create temporary directory for checkpoint tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def test_state():
    """Create test state for checkpoint tests."""
    return State(
        query="test query", user_id="test_user", iteration=1, selected_tools=[], tool_calls=[]
    )


class TestCheckpointDecorator:
    """Test the checkpoint decorator functionality."""

    @pytest.mark.asyncio
    async def test_decorator_passthrough_when_no_state(self):
        """Test decorator passes through when no state provided."""

        @checkpoint("test")
        async def test_func(data):
            return f"processed: {data}"

        result = await test_func("hello")
        assert result == "processed: hello"

    @pytest.mark.asyncio
    async def test_decorator_passthrough_when_not_interruptible(self, test_state):
        """Test decorator passes through when interruptible=False."""

        @checkpoint("test", interruptible=False)
        async def test_func(state):
            return f"processed: {state.query}"

        result = await test_func(test_state)
        assert result == "processed: test query"

    @pytest.mark.asyncio
    async def test_decorator_saves_checkpoint_when_interruptible(
        self, test_state, temp_checkpoint_dir
    ):
        """Test decorator saves checkpoint when interruptible=True."""

        # Use temporary checkpoint directory
        test_checkpointer = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        with patch("cogency.robust.checkpoint.checkpointer", test_checkpointer):

            @checkpoint("test", interruptible=True)
            async def test_func(state):
                return f"processed: {state.query}"

            result = await test_func(test_state)
            assert result == "processed: test query"

            # Verify checkpoint was saved
            fingerprint = test_checkpointer._generate_fingerprint(test_state)
            checkpoint_path = test_checkpointer._get_checkpoint_path(fingerprint)
            assert checkpoint_path.exists()

    @pytest.mark.asyncio
    async def test_decorator_saves_checkpoint_on_exception(self, test_state, temp_checkpoint_dir):
        """Test decorator saves checkpoint when function raises exception."""

        test_checkpointer = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        with patch("cogency.robust.checkpoint.checkpointer", test_checkpointer):

            @checkpoint("test", interruptible=True)
            async def test_func(state):
                raise ValueError("Test error")

            with pytest.raises(ValueError, match="Test error"):
                await test_func(test_state)

            # Verify checkpoint was still saved
            fingerprint = test_checkpointer._generate_fingerprint(test_state)
            checkpoint_path = test_checkpointer._get_checkpoint_path(fingerprint)
            assert checkpoint_path.exists()


class TestCheckpointClass:
    """Test the Checkpoint class functionality."""

    def test_checkpoint_init(self, temp_checkpoint_dir):
        """Test checkpoint initialization."""
        cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)
        assert cp.checkpoint_dir == temp_checkpoint_dir
        assert cp.checkpoint_dir.exists()

    def test_generate_fingerprint(self, temp_checkpoint_dir, test_state):
        """Test fingerprint generation is deterministic."""
        cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        fingerprint1 = cp._generate_fingerprint(test_state)
        fingerprint2 = cp._generate_fingerprint(test_state)

        assert fingerprint1 == fingerprint2
        assert len(fingerprint1) == 16  # SHA256 truncated to 16 chars

    def test_fingerprint_changes_with_state(self, temp_checkpoint_dir):
        """Test fingerprint changes when state changes."""
        cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        state1 = State(query="query1", iteration=1)
        state2 = State(query="query2", iteration=1)

        fingerprint1 = cp._generate_fingerprint(state1)
        fingerprint2 = cp._generate_fingerprint(state2)

        assert fingerprint1 != fingerprint2

    def test_save_and_load_checkpoint(self, temp_checkpoint_dir, test_state):
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

    def test_find_existing_checkpoint(self, temp_checkpoint_dir, test_state):
        """Test finding existing checkpoint."""
        cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        # Save checkpoint
        saved_fingerprint = cp.save(test_state, "test_type")

        # Find checkpoint
        found_fingerprint = cp.find(test_state)

        assert found_fingerprint == saved_fingerprint

    def test_find_nonexistent_checkpoint(self, temp_checkpoint_dir, test_state):
        """Test finding nonexistent checkpoint returns None."""
        cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        # Don't save anything
        found_fingerprint = cp.find(test_state)

        assert found_fingerprint is None


class TestResumeFunction:
    """Test the resume function in isolation."""

    def test_resume_with_no_checkpoint(self, temp_checkpoint_dir):
        """Test resume returns False when no checkpoint exists."""
        from cogency.robust.checkpoint import resume

        cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        with patch("cogency.robust.checkpoint.checkpointer", cp):
            state = State(query="no checkpoint", iteration=1)
            result = resume(state)
            assert result is False

    def test_resume_with_valid_checkpoint(self, temp_checkpoint_dir):
        """Test resume successfully restores state from checkpoint."""
        from cogency.robust.checkpoint import resume

        cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        # Create and save initial state
        original_state = State(
            query="resume test",
            iteration=3,
            mode="detailed",
            current_approach="test_approach",
            tool_calls=[{"name": "test_tool", "args": {}}],
            actions=[{"test": "action"}],
            attempts=[{"test": "attempt"}],
            messages=[{"role": "user", "content": "original message"}],
        )

        cp.save(original_state, "test_resume")

        # Create new state with same fingerprint signature (iteration affects fingerprint!)
        new_state = State(
            query="resume test",
            iteration=3,  # Must match for fingerprint to be same
            mode="fast",  # This will get overwritten by resume
            current_approach="initial",  # This will get overwritten by resume
        )

        with patch("cogency.robust.checkpoint.checkpointer", cp):
            result = resume(new_state)

            assert result is True
            assert new_state.iteration == 3
            assert new_state.mode == "detailed"
            assert new_state.current_approach == "test_approach"
            assert new_state.tool_calls == [{"name": "test_tool", "args": {}}]
            assert new_state.actions == [{"test": "action"}]
            assert new_state.attempts == [{"test": "attempt"}]

            # Should have original message plus resume message
            assert len(new_state.messages) == 2
            assert new_state.messages[0]["content"] == "original message"
            assert "RESUMING FROM CHECKPOINT" in new_state.messages[1]["content"]

    def test_resume_with_corrupted_checkpoint(self, temp_checkpoint_dir):
        """Test resume handles corrupted checkpoint gracefully."""
        from cogency.robust.checkpoint import resume

        cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

        # Create state and save checkpoint
        state = State(query="corrupt test", iteration=1)
        fingerprint = cp.save(state, "corrupt_test")

        # Corrupt the checkpoint file
        checkpoint_path = cp._get_checkpoint_path(fingerprint)
        with checkpoint_path.open("w") as f:
            f.write("invalid json content")

        # Create new state for resume
        new_state = State(query="corrupt test", iteration=1)

        with patch("cogency.robust.checkpoint.checkpointer", cp):
            result = resume(new_state)

            # Should fail gracefully without exceptions
            assert result is False


@pytest.mark.asyncio
async def test_integration_checkpoint_and_resume(temp_checkpoint_dir):
    """Integration test: save checkpoint and resume from it."""
    cp = Checkpoint(checkpoint_dir=temp_checkpoint_dir)

    # Create initial state
    state = State(query="integration test", iteration=2, selected_tools=[], tool_calls=[])

    # Save checkpoint
    fingerprint = cp.save(state, "integration_test")
    assert fingerprint is not None

    # Create new state with same signature
    new_state = State(query="integration test", iteration=2, selected_tools=[], tool_calls=[])

    # Should find the checkpoint
    found_fingerprint = cp.find(new_state)
    assert found_fingerprint == fingerprint

    # Should load the checkpoint data
    checkpoint_data = cp.load(found_fingerprint)
    assert checkpoint_data["query"] == "integration test"
    assert checkpoint_data["iteration"] == 2
