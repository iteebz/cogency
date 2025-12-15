import asyncio
from unittest.mock import AsyncMock

import pytest

from cogency.core.executor import execute_tool, execute_tools
from cogency.core.protocols import ToolCall, ToolResult


@pytest.mark.asyncio
async def test_successful_execution(mock_config, mock_tool):
    mock_tool = mock_tool(name="test_tool")
    mock_config.tools = [mock_tool]
    call = ToolCall(name="test_tool", args={"message": "test_value"})

    result = await execute_tool(
        call,
        execution=mock_config.execution,
        user_id="user1",
        conversation_id="conv1",
    )

    assert isinstance(result, ToolResult)
    assert "Tool executed: test_value" in result.outcome


@pytest.mark.asyncio
async def test_tool_not_found(mock_config):
    call = ToolCall(name="nonexistent", args={})

    result = await execute_tool(
        call,
        execution=mock_config.execution,
        user_id="user1",
        conversation_id="conv1",
    )

    assert result.outcome == "Tool 'nonexistent' not registered"
    assert result.error is True


# These validation tests removed - ToolCall structure guarantees valid format


@pytest.mark.asyncio
async def test_tool_execution_failure(mock_config, mock_tool):
    mock_tool = mock_tool(name="failing_tool", should_fail=True)
    mock_config.tools = [mock_tool]
    call = ToolCall(name="failing_tool", args={"message": "fail"})

    result = await execute_tool(
        call,
        execution=mock_config.execution,
        user_id="user1",
        conversation_id="conv1",
    )

    assert result.error is True
    assert "Tool execution failed" in result.outcome


# Removed - covered by test_tool_execution_failure


@pytest.mark.asyncio
async def test_context_injection(mock_config, mock_tool):
    mock_tool = mock_tool(name="context_tool")
    mock_tool.execute = AsyncMock(return_value=ToolResult(outcome="success"))

    mock_config.tools = [mock_tool]
    call = ToolCall(name="context_tool", args={"explicit_arg": "value"})

    await execute_tool(
        call,
        execution=mock_config.execution,
        user_id="test_user",
        conversation_id="test_conv",
    )

    call_kwargs = mock_tool.execute.call_args[1]
    assert call_kwargs["explicit_arg"] == "value"
    assert call_kwargs["sandbox_dir"] == ".cogency/sandbox"
    assert call_kwargs["access"] == "sandbox"
    assert call_kwargs["user_id"] == "test_user"
    assert "storage" in call_kwargs


@pytest.mark.asyncio
async def test_parallel_batch_execution_preserves_order(mock_config, mock_tool):
    """Multiple tools execute in parallel, results preserve input order."""
    mock_tool_instance = mock_tool(name="test_tool")
    mock_config.tools = [mock_tool_instance]

    calls = [
        ToolCall(name="test_tool", args={"message": "first"}),
        ToolCall(name="test_tool", args={"message": "second"}),
        ToolCall(name="test_tool", args={"message": "third"}),
    ]

    results = await execute_tools(
        calls,
        execution=mock_config.execution,
        user_id="user1",
        conversation_id="conv1",
    )

    assert len(results) == 3
    assert all(isinstance(r, ToolResult) for r in results)
    assert "first" in results[0].outcome
    assert "second" in results[1].outcome
    assert "third" in results[2].outcome


@pytest.mark.asyncio
async def test_parallel_execution_is_concurrent(mock_config):
    """Verify tools actually run in parallel, not sequentially."""
    execution_order = []

    class SlowTool:
        name = "slow_tool"
        description = "A slow tool"
        schema = {}

        async def execute(self, delay=0.1, **kwargs):
            execution_order.append(f"start_{delay}")
            await asyncio.sleep(delay)
            execution_order.append(f"end_{delay}")
            return ToolResult(outcome=f"done_{delay}")

        def describe(self, args):
            return "slow"

    mock_config.tools = [SlowTool()]

    calls = [
        ToolCall(name="slow_tool", args={"delay": 0.1}),
        ToolCall(name="slow_tool", args={"delay": 0.05}),
    ]

    results = await execute_tools(
        calls,
        execution=mock_config.execution,
        user_id="user1",
        conversation_id="conv1",
    )

    assert len(results) == 2
    # If parallel: both start before either ends
    # execution_order should be: start_0.1, start_0.05, end_0.05, end_0.1
    assert execution_order[0] == "start_0.1"
    assert execution_order[1] == "start_0.05"
    # The shorter one finishes first
    assert execution_order[2] == "end_0.05"
    assert execution_order[3] == "end_0.1"
    # But results preserve input order
    assert results[0].outcome == "done_0.1"
    assert results[1].outcome == "done_0.05"
