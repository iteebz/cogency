"""Test Output business logic."""

from unittest.mock import AsyncMock

import pytest

from cogency.output import Output


@pytest.mark.asyncio
async def test_output_tracing():
    """Test trace functionality."""
    callback = AsyncMock()
    output = Output(trace=True, callback=callback)

    await output.trace("test message", node="test_node", extra="data")

    assert len(output.entries) == 1
    entry = output.entries[0]
    assert entry["type"] == "trace"
    assert entry["message"] == "test message"
    assert entry["node"] == "test_node"
    assert entry["extra"] == "data"

    callback.assert_called_once_with("\n  ➡️ [test_node] test message")


@pytest.mark.asyncio
async def test_output_verbose():
    """Test verbose output."""
    callback = AsyncMock()
    output = Output(verbose=True, callback=callback)

    await output.update("test message", type="reasoning")

    callback.assert_called_once_with("\ntest message")
