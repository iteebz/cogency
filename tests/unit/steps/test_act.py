"""Test Act node - tool execution logic."""

from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency.state import State
from cogency.steps.act import act


@pytest.fixture
def state():
    return State(query="test query", debug=True)


@pytest.mark.asyncio
async def test_none(state, tools):
    """Test act node when no tool calls are present."""
    state.tool_calls = None
    await act(state, AsyncMock(), tools=tools)
    assert not state.latest_tool_results  # No tool results should be added


@pytest.mark.asyncio
async def test_empty(state, tools):
    """Test act node with empty tool call list."""
    state.tool_calls = []
    await act(state, AsyncMock(), tools=tools)
    assert not state.latest_tool_results


@pytest.mark.asyncio
async def test_invalid(state, tools):
    """Test act node with invalid tool calls format (not a list)."""
    state.tool_calls = "invalid json"
    await act(state, AsyncMock(), tools=tools)
    assert not state.latest_tool_results


@pytest.mark.asyncio
async def test_success(state, tools):
    """Test successful tool execution."""
    state.tool_calls = [{"name": "mock_tool", "args": {"x": 5}}]
    state.add_action(
        mode="fast",
        thinking="test",
        planning="test",
        reflection="test",
        approach="test",
        tool_calls=state.tool_calls,
    )

    await act(state, AsyncMock(), tools=tools)

    assert len(state.latest_tool_results) == 1
    result = state.latest_tool_results[0]
    assert result["name"] == "mock_tool"
    assert result["outcome"] == "success"


@pytest.mark.asyncio
async def test_failure(state, mock_tool):
    """Test handling of failed tool execution."""

    # Mock the tool to fail
    async def failing_run(**kwargs):
        return Result.fail("Tool failed")

    mock_tool.run = failing_run
    state.tool_calls = [{"name": "mock_tool", "args": {}}]
    state.add_action(
        mode="fast",
        thinking="test",
        planning="test",
        reflection="test",
        approach="test",
        tool_calls=state.tool_calls,
    )

    await act(state, AsyncMock(), tools=[mock_tool])

    assert len(state.latest_tool_results) == 1
    result = state.latest_tool_results[0]
    assert result["name"] == "mock_tool"
    assert result["outcome"] == "failure"
    assert "Tool failed" in result["result"]


@pytest.mark.asyncio
async def test_multi(state, tools):
    """Test execution of multiple tools in sequence."""
    # Use single tool multiple times for simplicity
    state.tool_calls = [
        {"name": "mock_tool", "args": {}},
        {"name": "mock_tool", "args": {}},
        {"name": "mock_tool", "args": {}},
    ]
    state.add_action(
        mode="fast",
        thinking="test",
        planning="test",
        reflection="test",
        approach="test",
        tool_calls=state.tool_calls,
    )

    await act(state, AsyncMock(), tools=tools)

    assert len(state.latest_tool_results) == 3
    assert all(result["name"] == "mock_tool" for result in state.latest_tool_results)
    assert all(result["outcome"] == "success" for result in state.latest_tool_results)
