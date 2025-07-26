"""Test Act node - tool execution logic."""

from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest

from cogency.context import Context
from cogency.nodes.act import act
from cogency.output import Output
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.utils.results import ToolResult


class MockTool(BaseTool):
    """Simple mock tool."""

    def __init__(self, name: str, should_succeed: bool = True, result: ToolResult = None):
        super().__init__(
            name=name,
            description=f"Mock {name}",
            emoji="🧪",
            schema='{"type": "object"}',
            examples=[f'{{"name": "{name}", "args": {{}}}}'],
        )
        self.should_succeed = should_succeed
        self.result = result or ToolResult("mock result")

    async def run(self, **kwargs):
        if not self.should_succeed:
            raise Exception("Tool failed")
        return self.result

    def format_human(self, params, results=None):
        param_str = f"({', '.join(f'{k}={v}' for k, v in params.items())})" if params else "()"
        result_str = str(results) if results else "pending"
        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        return f"Tool output: {result_data}"


@pytest.fixture
def output():
    output = Output(trace=True)
    output.send = AsyncMock()  # Mock the send method
    output.update = AsyncMock()  # Mock the update method
    return output


@pytest.fixture
def state(output):
    context = Context("test query")
    return State(context=context, query="test query", output=output)


@pytest.fixture
def mock_tools():
    return [
        MockTool("calculator", True, ToolResult({"result": 42})),
        MockTool("search", True, ToolResult({"results": ["data"]})),
    ]


@pytest.mark.asyncio
async def test_no_tool_calls(state, mock_tools):
    """Test act node when no tool calls are present."""
    state["tool_calls"] = None

    result = await act(state, tools=mock_tools)

    assert result["result"].data["type"] == "no_action"


@pytest.mark.asyncio
async def test_empty_tool_calls(state, mock_tools):
    """Test act node with empty tool call string."""
    state["tool_calls"] = ""

    result = await act(state, tools=mock_tools)

    assert result["result"].data["type"] == "no_action"


@pytest.mark.asyncio
async def test_invalid_tool_calls(state, mock_tools):
    """Test act node with invalid JSON tool calls."""
    state["tool_calls"] = "invalid json"

    result = await act(state, tools=mock_tools)

    assert result["result"].data["type"] == "no_action"


@pytest.mark.asyncio
async def test_successful_tool_execution(state, mock_tools):
    """Test successful tool execution."""
    state["tool_calls"] = [{"name": "calculator", "args": {"x": 5}}]

    result = await act(state, tools=mock_tools)

    assert "result" in result
    # Should have successful execution
    exec_results = result["result"].data
    if "successful_count" in exec_results:
        assert exec_results["successful_count"] >= 1


@pytest.mark.asyncio
async def test_failed_tool_execution(state):
    """Test handling of failed tool execution."""
    failing_tool = MockTool("failing_tool", should_succeed=False)
    state["tool_calls"] = [{"name": "failing_tool", "args": {}}]

    result = await act(state, tools=[failing_tool])

    exec_results = result["result"].data
    if "successful_count" in exec_results:
        assert exec_results["successful_count"] == 0


@pytest.mark.asyncio
async def test_multiple_tool_execution(state, output):
    """Test execution of multiple tools in sequence."""
    # Create tools that track execution order
    execution_order = []

    class OrderedTool(BaseTool):
        def __init__(self, name: str):
            super().__init__(
                name=name,
                description=f"Tool {name}",
                emoji="🔧",
                schema='{"type": "object"}',
                examples=[],
            )

        async def run(self, **kwargs):
            execution_order.append(self.name)
            return ToolResult(f"{self.name}_result")

        def format_human(self, params, results=None):
            param_str = f"({', '.join(f'{k}={v}' for k, v in params.items())})" if params else "()"
            result_str = str(results) if results else "pending"
            return param_str, result_str

        def format_agent(self, result_data: dict[str, any]) -> str:
            return f"Tool output: {result_data}"

    tools = [OrderedTool("first"), OrderedTool("second"), OrderedTool("third")]

    state["tool_calls"] = [
        {"name": "first", "args": {}},
        {"name": "second", "args": {}},
        {"name": "third", "args": {}},
    ]

    result = await act(state, tools=tools)

    # Check that tools executed in order
    assert execution_order == ["first", "second", "third"]

    # Check execution results
    exec_results = result["result"].data
    assert exec_results["successful_count"] == 3
    assert exec_results["failed_count"] == 0
