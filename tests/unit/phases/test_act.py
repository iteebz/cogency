"""Test Act node - tool execution logic."""

from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest
from resilient_result import Result, unwrap

from cogency.phases.act import act
from cogency.state import State
from cogency.tools.base import Tool
from cogency.types.tools import ToolOutcome


class MockTool(Tool):
    """Simple mock tool."""

    def __init__(self, name: str, should_succeed: bool = True, result: Result = None):
        super().__init__(
            name=name,
            description=f"Mock {name}",
            emoji="🧪",
            examples=[f'{{"name": "{name}", "args": {{}}}}'],
        )
        self.should_succeed = should_succeed
        self.result = result or Result.ok("mock result")

    async def run(self, **kwargs):
        if not self.should_succeed:
            return Result.err("Tool failed")
        return self.result

    def format_human(self, params, results=None):
        param_str = f"({', '.join(f'{k}={v}' for k, v in params.items())})" if params else "()"
        result_str = str(results) if results else "pending"
        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        return f"Tool output: {result_data}"


@pytest.fixture
def state():
    return State(query="test query", debug=True)


@pytest.fixture
def mock_tools():
    return [
        MockTool("calculator", True, Result.ok({"result": 42})),
        MockTool("search", True, Result.ok({"results": ["data"]})),
    ]


@pytest.mark.asyncio
async def test_no_calls(state, mock_tools):
    """Test act node when no tool calls are present."""
    state.tool_calls = None
    await act(state, tools=mock_tools)
    assert not state.latest_tool_results  # No tool results should be added


@pytest.mark.asyncio
async def test_empty_calls(state, mock_tools):
    """Test act node with empty tool call list."""
    state.tool_calls = []
    await act(state, tools=mock_tools)
    assert not state.latest_tool_results


@pytest.mark.asyncio
async def test_invalid_calls_format(state, mock_tools):
    """Test act node with invalid tool calls format (not a list)."""
    state.tool_calls = "invalid json"
    await act(state, tools=mock_tools)
    assert not state.latest_tool_results


@pytest.mark.asyncio
async def test_success(state, mock_tools):
    """Test successful tool execution."""
    state.tool_calls = [{"name": "calculator", "args": {"x": 5}}]
    state.add_action(
        mode="fast",
        thinking="test",
        planning="test",
        reflection="test",
        approach="test",
        tool_calls=state.tool_calls,
    )

    await act(state, tools=mock_tools)

    assert len(state.latest_tool_results) == 1
    result = state.latest_tool_results[0]
    assert result.name == "calculator"
    assert result.success
    assert "42" in result.result


@pytest.mark.asyncio
async def test_failure(state):
    """Test handling of failed tool execution."""
    failing_tool = MockTool("failing_tool", should_succeed=False)
    state.tool_calls = [{"name": "failing_tool", "args": {}}]
    state.add_action(
        mode="fast",
        thinking="test",
        planning="test",
        reflection="test",
        approach="test",
        tool_calls=state.tool_calls,
    )

    await act(state, tools=[failing_tool])

    assert len(state.latest_tool_results) == 1
    result = state.latest_tool_results[0]
    assert result.name == "failing_tool"
    assert not result.success
    assert "missing required information" in result.result


@pytest.mark.asyncio
async def test_multiple(state):
    """Test execution of multiple tools in sequence."""
    tools = [MockTool("first"), MockTool("second"), MockTool("third")]
    state.tool_calls = [
        {"name": "first", "args": {}},
        {"name": "second", "args": {}},
        {"name": "third", "args": {}},
    ]
    state.add_action(
        mode="fast",
        thinking="test",
        planning="test",
        reflection="test",
        approach="test",
        tool_calls=state.tool_calls,
    )

    await act(state, tools=tools)

    assert len(state.latest_tool_results) == 3
    assert state.latest_tool_results[0].name == "first"
    assert state.latest_tool_results[1].name == "second"
    assert state.latest_tool_results[2].name == "third"
    assert all(result.success for result in state.latest_tool_results)
