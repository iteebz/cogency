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
    assert result.data["summary"] == "No tools to execute"
    assert result.data["results"] == []
    assert result.data["errors"] == []
    assert result.data["total_executed"] == 0


@pytest.mark.asyncio
async def test_successful_execution():
    """Test successful tool execution."""
    # Mock tool
    mock_tool = Mock()
    mock_tool.name = "test_tool"
    mock_tool.execute = AsyncMock(return_value=Result.ok({"data": "success"}))

    tools = [mock_tool]
    state = Mock()
    state.execution = Mock()

    tool_calls = [{"name": "test_tool", "args": {"param": "value"}}]

    with patch("cogency.events.emit") as mock_emit:
        result = await act(tool_calls, tools, state)

        assert result.success
        assert result.data["successful_count"] == 1
        assert result.data["failed_count"] == 0
        assert "1 tools executed successfully" in result.data["summary"]

        # Verify tool was called correctly
        mock_tool.execute.assert_called_once_with(param="value")

        # Verify events were emitted
        mock_emit.assert_called()

        # Verify state was updated
        assert hasattr(state.execution, "completed_calls")
        assert len(state.execution.completed_calls) == 1


@pytest.mark.asyncio
async def test_tool_not_found():
    """Test act with non-existent tool."""
    tools = []
    state = Mock()

    tool_calls = [{"name": "nonexistent_tool", "args": {}}]

    result = await act(tool_calls, tools, state)

    assert result.success
    assert result.data["successful_count"] == 0
    assert result.data["failed_count"] == 1
    assert "Tool 'nonexistent_tool' not found" in result.data["errors"][0]["error"]


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

    with patch("cogency.events.emit") as mock_emit:
        result = await act(tool_calls, tools, state)

        assert result.success  # act() succeeds even if tools fail
        assert result.data["successful_count"] == 0
        assert result.data["failed_count"] == 1
        assert "Tool failed" in result.data["errors"][0]["error"]

        # Verify failure event was emitted
        failure_calls = [call for call in mock_emit.call_args_list if "ok=False" in str(call)]
        assert len(failure_calls) > 0


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
        assert result.data["successful_count"] == 0
        assert result.data["failed_count"] == 1
        assert "Execution error" in result.data["errors"][0]["error"]

        # Verify error result was created
        error_result = result.data["errors"][0]["result"]
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
    assert result.data["successful_count"] == 1
    assert result.data["failed_count"] == 1
    assert "1 tools executed successfully; 1 tools failed" in result.data["summary"]


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
    state_with_exec.execution = Mock()

    result = await act(tool_calls, tools, state_with_exec)
    assert result.success
    assert hasattr(state_with_exec.execution, "completed_calls")
    assert len(state_with_exec.execution.completed_calls) == 1

    completed_call = state_with_exec.execution.completed_calls[0]
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
async def test_event_emissions():
    """Test proper event emissions during execution."""
    mock_tool = Mock()
    mock_tool.name = "event_tool"
    mock_tool.execute = AsyncMock(return_value=Result.ok({"data": "test_data"}))

    tools = [mock_tool]
    state = Mock()
    tool_calls = [{"name": "event_tool", "args": {}}]

    with patch("cogency.events.emit") as mock_emit:
        await act(tool_calls, tools, state)

        # Should emit action start and tool success events
        emit_calls = mock_emit.call_args_list

        # Check for action execution event
        action_calls = [call for call in emit_calls if call[0][0] == "action"]
        assert len(action_calls) >= 1
        assert action_calls[0][1]["state"] == "executing"
        assert action_calls[0][1]["tool"] == "event_tool"

        # Check for tool success event
        tool_calls = [call for call in emit_calls if call[0][0] == "tool"]
        assert len(tool_calls) >= 1
        assert tool_calls[0][1]["name"] == "event_tool"
        assert tool_calls[0][1]["ok"] is True


@pytest.mark.asyncio
async def test_data_truncation():
    """Test result data truncation in events."""
    long_data = "x" * 300  # Longer than 200 char limit

    mock_tool = Mock()
    mock_tool.name = "long_tool"
    mock_tool.execute = AsyncMock(return_value=Result.ok(long_data))

    tools = [mock_tool]
    state = Mock()
    tool_calls = [{"name": "long_tool", "args": {}}]

    with patch("cogency.events.emit") as mock_emit:
        await act(tool_calls, tools, state)

        # Find tool success event
        tool_events = [
            call
            for call in mock_emit.call_args_list
            if len(call[0]) > 0 and call[0][0] == "tool" and call[1].get("ok")
        ]

        assert len(tool_events) >= 1
        result_str = tool_events[0][1]["result"]
        assert len(result_str) <= 200  # Should be truncated
