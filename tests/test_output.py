"""Test Output business logic."""
import pytest
from unittest.mock import AsyncMock

from cogency.output import Output, tool_emoji, emoji


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
    
    callback.assert_called_once_with("🔮   [test_node] test message")


@pytest.mark.asyncio
async def test_output_verbose():
    """Test verbose output."""
    callback = AsyncMock()
    output = Output(verbose=True, callback=callback)
    
    await output.update("test message", type="reasoning")
    
    callback.assert_called_once_with("🤔 test message")


@pytest.mark.asyncio
async def test_tool_logging():
    """Test tool execution logging."""
    callback = AsyncMock()
    output = Output(verbose=True, callback=callback)
    
    # Success case
    await output.log_tool("calculator", {"result": 42}, success=True)
    call_args = callback.call_args[0][0]
    assert "⚡ calculator" in call_args
    assert "✅" in call_args
    
    # Failure case
    await output.log_tool("calculator", "error message", success=False)
    call_args = callback.call_args[0][0]
    assert "⚡ calculator" in call_args
    assert "❌" in call_args


def test_emoji_mappings():
    """Test emoji functions."""
    assert tool_emoji("memory") == "🧠"
    assert tool_emoji("unknown_tool") == "⚡"
    assert emoji["reason"] == "🧠"
    assert emoji["act"] == "⚡"