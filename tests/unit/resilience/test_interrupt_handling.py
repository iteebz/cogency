"""Test proper async interrupt handling."""

import asyncio
import os
import signal
from unittest.mock import Mock, patch

import pytest

from cogency.resilience.utils import interruptible_context
from cogency.resilience import safe
from cogency.state import State


@pytest.mark.asyncio
async def test_interruptible_context_signal_handling():
    """Test interruptible context properly handles SIGINT."""

    async with interruptible_context() as interrupt_event:
        # Send interrupt in separate task to avoid cancelling ourselves
        async def send_signal():
            await asyncio.sleep(0.01)  # Brief delay
            os.kill(os.getpid(), signal.SIGINT)

        signal_task = asyncio.create_task(send_signal())

        # Expect to be cancelled by the signal
        with pytest.raises(asyncio.CancelledError):
            await asyncio.sleep(0.1)  # This will be cancelled

        await signal_task  # Ensure signal was sent
        assert interrupt_event.is_set()


@pytest.mark.asyncio
async def test_checkpoint_saves_on_interrupt():
    """Test checkpoint is saved when function is interrupted."""

    @safe.checkpoint("test", interruptible=True)
    async def slow_function(state):
        # Simulate long-running operation
        await asyncio.sleep(0.1)
        return "completed"

    state = Mock(spec=State)
    state.get.side_effect = lambda key, default=None: {"query": "test"}.get(key, default)
    state.flow = {"selected_tools": []}
    state.selected_tools = []

    # Mock checkpoint manager to verify save is called
    with patch("cogency.resilience.checkpoint.checkpoints") as mock_checkpoints:
        # Send interrupt after brief delay
        async def send_interrupt():
            await asyncio.sleep(0.02)
            os.kill(os.getpid(), signal.SIGINT)

        # Run both tasks concurrently
        interrupt_task = asyncio.create_task(send_interrupt())

        with pytest.raises(asyncio.CancelledError):
            await slow_function(state)

        await interrupt_task  # Ensure interrupt was sent

        # Verify checkpoint was saved with interrupt type
        mock_checkpoints.save_checkpoint.assert_called()
        args, kwargs = mock_checkpoints.save_checkpoint.call_args
        assert "interrupted" in args[1]  # checkpoint_type should contain "interrupted"


@pytest.mark.asyncio
async def test_non_interruptible_checkpoint_works_normally():
    """Test normal checkpoint without interrupt handling."""

    @safe.checkpoint("test", interruptible=False)
    async def normal_function(state):
        return "success"

    state = Mock(spec=State)
    state.get.side_effect = lambda key, default=None: {"query": "test"}.get(key, default)
    state.flow = {"selected_tools": []}
    state.selected_tools = []

    result = await normal_function(state)
    assert result == "success"
