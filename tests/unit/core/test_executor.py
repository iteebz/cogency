"""Tool execution tests with context injection and error handling."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from cogency.core.executor import execute
from cogency.core.protocols import ToolCall, ToolResult


@pytest.mark.asyncio
async def test_successful_execution(mock_config, mock_tool):
    """Tool executes successfully with proper result structure."""
    mock_config.tools = [mock_tool.configure(name="test_tool")]
    call = ToolCall(name="test_tool", args={"message": "test_value"})

    result = await execute(call, mock_config, "user1", "conv1")

    assert isinstance(result, ToolResult)
    assert "Tool executed: test_value" in result.outcome


@pytest.mark.asyncio
async def test_tool_not_found(mock_config):
    """Missing tool returns proper error."""
    call = ToolCall(name="nonexistent", args={})

    result = await execute(call, mock_config, "user1", "conv1")

    assert result.outcome == "nonexistent not found: Tool 'nonexistent' not registered"


# These validation tests removed - ToolCall structure guarantees valid format


@pytest.mark.asyncio
async def test_tool_execution_failure(mock_config, mock_tool):
    """Tool returning Err() handled properly."""
    mock_config.tools = [mock_tool.configure(name="failing_tool", should_fail=True)]
    call = ToolCall(name="failing_tool", args={"message": "fail"})

    # Tool execution fails - should bubble up as system error
    with pytest.raises(RuntimeError, match="Tool execution failed"):
        await execute(call, mock_config, "user1", "conv1")


# Removed - covered by test_tool_execution_failure


@pytest.mark.asyncio
async def test_context_injection(mock_config):
    """Global context (sandbox, user_id) injected into tool args."""
    mock_tool = MagicMock()
    mock_tool.name = "context_tool"
    mock_tool.execute = AsyncMock(return_value=ToolResult(outcome="success"))

    mock_config.tools = [mock_tool]
    call = ToolCall(name="context_tool", args={"explicit_arg": "value"})

    await execute(call, mock_config, "test_user", "test_conv")

    mock_tool.execute.assert_called_once_with(explicit_arg="value", user_id="test_user")
