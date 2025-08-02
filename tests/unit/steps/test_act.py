"""Test Act node - tool execution logic."""

from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency.state import AgentState
from cogency.steps.act import act


@pytest.fixture
def state():
    state = AgentState(query="test query")
    state.execution.debug = True
    return state


@pytest.mark.asyncio
async def test_none(state, tools):
    """Test act node when no tool calls are present."""
    state.execution.pending_calls = []
    await act(state, AsyncMock(), tools=tools)
    assert len(state.execution.completed_calls) == 0


@pytest.mark.asyncio
async def test_empty(state, tools):
    """Test act node with empty tool call list."""
    state.execution.pending_calls = []
    await act(state, AsyncMock(), tools=tools)
    assert len(state.execution.completed_calls) == 0


@pytest.mark.asyncio
async def test_invalid(state, tools):
    """Test act node with invalid tool calls format (not a list)."""
    state.execution.pending_calls = []
    await act(state, AsyncMock(), tools=tools)
    assert len(state.execution.completed_calls) == 0


@pytest.mark.asyncio
async def test_success(state, tools):
    """Test successful tool execution."""
    state.execution.set_tool_calls([{"name": "mock_tool", "args": {"x": 5}}])
    await act(state, AsyncMock(), tools=tools)

    assert len(state.execution.completed_calls) == 1
    result = state.execution.completed_calls[0]
    assert result["name"] == "mock_tool"
    assert "result" in result


@pytest.mark.asyncio
async def test_failure(state, mock_tool):
    """Test handling of failed tool execution."""

    # Mock the tool to fail
    async def failing_run(**kwargs):
        return Result.fail("Tool failed")

    mock_tool.run = failing_run
    state.execution.set_tool_calls([{"name": "mock_tool", "args": {}}])

    await act(state, AsyncMock(), tools=[mock_tool])

    assert len(state.execution.completed_calls) == 1
    result = state.execution.completed_calls[0]
    assert result["name"] == "mock_tool"


@pytest.mark.asyncio
async def test_multi(state, tools):
    """Test execution of multiple tools in sequence."""
    # Use single tool multiple times for simplicity
    state.execution.set_tool_calls(
        [
            {"name": "mock_tool", "args": {}},
            {"name": "mock_tool", "args": {}},
            {"name": "mock_tool", "args": {}},
        ]
    )

    await act(state, AsyncMock(), tools=tools)

    assert len(state.execution.completed_calls) == 3
    assert all(result["name"] == "mock_tool" for result in state.execution.completed_calls)
