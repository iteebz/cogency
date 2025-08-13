"""Tests for tool execution logic."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from resilient_result import Result

from cogency.agents.act import _find_tool, act


@pytest.mark.asyncio
async def test_empty_calls():
    """Test act with empty tool calls list."""
    result = await act([], [], Mock())

    assert result.success
    assert result.unwrap()["summary"] == "No tools to execute"
    assert result.unwrap()["results"] == []
    assert result.unwrap()["errors"] == []
    assert result.unwrap()["total_executed"] == 0


@pytest.mark.asyncio
async def test_successful_execution():
    """Test successful tool execution."""
    # Mock tool
    mock_tool = Mock()
    mock_tool.name = "test_tool"
    mock_tool.execute = AsyncMock(return_value=Result.ok({"data": "success"}))

    tools = [mock_tool]
    state = Mock()
    # Create execution as a simple object that doesn't have completed_calls initially
    state.execution = type("Execution", (), {})()  # Simple object without completed_calls

    tool_calls = [{"name": "test_tool", "args": {"param": "value"}}]

    result = await act(tool_calls, tools, state)

    assert result.success
    assert result.unwrap()["successful_count"] == 1
    assert result.unwrap()["failed_count"] == 0
    assert "1 tools executed successfully" in result.unwrap()["summary"]

    # Verify tool was called correctly
    mock_tool.execute.assert_called_once_with(param="value")

    # Verify state was updated - act() creates completed_calls as a list
    assert hasattr(state.execution, "completed_calls")
    calls = state.execution.completed_calls
    assert isinstance(calls, list)
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_tool_not_found():
    """Test act with non-existent tool."""
    tools = []
    state = Mock()

    tool_calls = [{"name": "nonexistent_tool", "args": {}}]

    result = await act(tool_calls, tools, state)

    assert result.success
    assert result.unwrap()["successful_count"] == 0
    assert result.unwrap()["failed_count"] == 1
    assert "Tool 'nonexistent_tool' not found" in result.unwrap()["errors"][0]["error"]


@pytest.mark.asyncio
async def test_execution_failure():
    """Test tool execution returning failure result."""
    # Mock tool that fails
    mock_tool = Mock()
    mock_tool.name = "failing_tool"
    mock_tool.execute = AsyncMock(return_value=Result.fail("Tool failed"))

    tools = [mock_tool]
    state = Mock()

    tool_calls = [{"name": "failing_tool", "args": {}}]

    result = await act(tool_calls, tools, state)

    assert result.success  # act() succeeds even if tools fail
    assert result.unwrap()["successful_count"] == 0
    assert result.unwrap()["failed_count"] == 1
    assert "Tool failed" in result.unwrap()["errors"][0]["error"]


@pytest.mark.asyncio
async def test_execution_exception():
    """Test tool execution raising exception."""
    # Mock tool that raises exception
    mock_tool = Mock()
    mock_tool.name = "exception_tool"
    mock_tool.execute = AsyncMock(side_effect=Exception("Execution error"))

    tools = [mock_tool]
    state = Mock()

    tool_calls = [{"name": "exception_tool", "args": {}}]

    with patch("cogency.events.emit"):
        result = await act(tool_calls, tools, state)

        assert result.success
        assert result.unwrap()["successful_count"] == 0
        assert result.unwrap()["failed_count"] == 1
        assert "Execution error" in result.unwrap()["errors"][0]["error"]

        # Verify error result was created
        error_result = result.unwrap()["errors"][0]["result"]
        assert error_result.failure


@pytest.mark.asyncio
async def test_mixed_results():
    """Test mix of successful and failing tool executions."""
    # Mock successful tool
    success_tool = Mock()
    success_tool.name = "success_tool"
    success_tool.execute = AsyncMock(return_value=Result.ok({"data": "success"}))

    # Mock failing tool
    fail_tool = Mock()
    fail_tool.name = "fail_tool"
    fail_tool.execute = AsyncMock(return_value=Result.fail("failure"))

    tools = [success_tool, fail_tool]
    state = Mock()
    state.execution = Mock()

    tool_calls = [
        {"name": "success_tool", "args": {}},
        {"name": "fail_tool", "args": {}},
    ]

    result = await act(tool_calls, tools, state)

    assert result.success
    assert result.unwrap()["successful_count"] == 1
    assert result.unwrap()["failed_count"] == 1
    assert "1 tools executed successfully; 1 tools failed" in result.unwrap()["summary"]


@pytest.mark.asyncio
async def test_state_tracking():
    """Test state update with completed calls tracking."""
    mock_tool = Mock()
    mock_tool.name = "state_tool"
    mock_tool.execute = AsyncMock(return_value=Result.ok({"result": "data"}))

    tools = [mock_tool]

    # State without execution attribute
    state_no_exec = Mock(spec=[])
    tool_calls = [{"name": "state_tool", "args": {"test": "value"}}]

    result = await act(tool_calls, tools, state_no_exec)
    assert result.success

    # State with execution but no completed_calls
    state_with_exec = Mock()
    state_with_exec.execution = type("Execution", (), {})()

    result = await act(tool_calls, tools, state_with_exec)
    assert result.success
    assert hasattr(state_with_exec.execution, "completed_calls")
    # completed_calls should be a list with one item
    calls = state_with_exec.execution.completed_calls
    assert isinstance(calls, list)
    assert len(calls) == 1

    completed_call = calls[0]
    assert completed_call["tool"] == "state_tool"
    assert completed_call["args"] == {"test": "value"}
    assert completed_call["success"] is True


@pytest.mark.asyncio
async def test_args_handling():
    """Test proper handling of tool arguments."""
    mock_tool = Mock()
    mock_tool.name = "args_tool"
    mock_tool.execute = AsyncMock(return_value=Result.ok({}))

    tools = [mock_tool]
    state = Mock()

    # Test with arguments
    tool_calls = [{"name": "args_tool", "args": {"param1": "value1", "param2": 42}}]

    result = await act(tool_calls, tools, state)

    assert result.success
    mock_tool.execute.assert_called_once_with(param1="value1", param2=42)

    # Test with no args key
    mock_tool.execute.reset_mock()
    tool_calls = [{"name": "args_tool"}]

    result = await act(tool_calls, tools, state)

    assert result.success
    mock_tool.execute.assert_called_once_with()  # Called with no args


def test_find_tool():
    """Test _find_tool helper function."""
    tool1 = Mock()
    tool1.name = "tool_one"

    tool2 = Mock()
    tool2.name = "tool_two"

    tools = [tool1, tool2]

    # Find existing tool
    found = _find_tool("tool_one", tools)
    assert found is tool1

    found = _find_tool("tool_two", tools)
    assert found is tool2

    # Tool not found
    found = _find_tool("nonexistent", tools)
    assert found is None

    # Empty tools list
    found = _find_tool("any", [])
    assert found is None


@pytest.mark.asyncio
async def test_basic_execution():
    """Test basic tool execution without events."""
    mock_tool = Mock()
    mock_tool.name = "basic_tool"
    mock_tool.execute = AsyncMock(return_value=Result.ok({"data": "test_data"}))

    tools = [mock_tool]
    state = Mock()
    tool_calls = [{"name": "basic_tool", "args": {}}]

    result = await act(tool_calls, tools, state)

    assert result.success
    assert result.unwrap()["successful_count"] == 1
    assert result.unwrap()["failed_count"] == 0
    assert "basic_tool" in result.unwrap()["results"][0]["name"]


@pytest.mark.asyncio
async def test_large_result_handling():
    """Test handling of large result data."""
    long_data = "x" * 1000  # Large data

    mock_tool = Mock()
    mock_tool.name = "large_tool"
    mock_tool.execute = AsyncMock(return_value=Result.ok({"large_data": long_data}))

    tools = [mock_tool]
    state = Mock()
    tool_calls = [{"name": "large_tool", "args": {}}]

    result = await act(tool_calls, tools, state)

    assert result.success
    assert result.unwrap()["successful_count"] == 1
    # Verify result contains the tool execution result
    tool_result = result.unwrap()["results"][0]["result"]
    assert tool_result.success
    assert len(tool_result.unwrap()["large_data"]) == 1000
