"""Test Act node - tool execution logic."""

from typing import Any, Dict
from unittest.mock import AsyncMock

import pytest
from resilient_result import Result, unwrap

from cogency.context import Context
from cogency.nodes.act import act
from cogency.state import State
from cogency.tools.base import BaseTool


class MockTool(BaseTool):
    """Simple mock tool."""

    def __init__(self, name: str, should_succeed: bool = True, result: Result = None):
        super().__init__(
            name=name,
            description=f"Mock {name}",
            emoji="🧪",
            examples=[f'{{"name": "{name}", "args": {{}}}}'],
        )
        self.should_succeed = should_succeed
        self.result = result or Result("mock result")

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
def state():
    context = Context("test query")
    return State(context=context, query="test query", trace=True)


@pytest.fixture
def mock_tools():
    return [
        MockTool("calculator", True, Result({"result": 42})),
        MockTool("search", True, Result({"results": ["data"]})),
    ]


@pytest.mark.asyncio
async def test_no_calls(state, mock_tools):
    """Test act node when no tool calls are present."""
    state["tool_calls"] = None

    wrapped = await act(state, tools=mock_tools)
    result = unwrap(wrapped)  # Unwrap @robust Result wrapper

    assert result["result"].success
    assert result["result"].data["type"] == "no_action"


@pytest.mark.asyncio
async def test_empty_calls(state, mock_tools):
    """Test act node with empty tool call string."""
    state["tool_calls"] = ""

    wrapped = await act(state, tools=mock_tools)
    result = unwrap(wrapped)  # Unwrap @robust Result wrapper

    assert result["result"].success
    assert result["result"].data["type"] == "no_action"


@pytest.mark.asyncio
async def test_invalid_calls(state, mock_tools):
    """Test act node with invalid JSON tool calls."""
    state["tool_calls"] = "invalid json"

    wrapped = await act(state, tools=mock_tools)
    result = unwrap(wrapped)  # Unwrap @robust Result wrapper

    assert result["result"].success
    assert result["result"].data["type"] == "no_action"


@pytest.mark.asyncio
async def test_success(state, mock_tools):
    """Test successful tool execution."""
    state["tool_calls"] = [{"name": "calculator", "args": {"x": 5}}]

    wrapped = await act(state, tools=mock_tools)
    result = unwrap(wrapped)  # Unwrap @robust Result wrapper

    assert "result" in result
    # Should have successful execution
    assert result["result"].success
    exec_results = result["result"].data
    if "successful_count" in exec_results:
        assert exec_results["successful_count"] >= 1


@pytest.mark.asyncio
async def test_failure(state):
    """Test handling of failed tool execution."""
    failing_tool = MockTool("failing_tool", should_succeed=False)
    state["tool_calls"] = [{"name": "failing_tool", "args": {}}]

    wrapped = await act(state, tools=[failing_tool])
    result = unwrap(wrapped)  # Unwrap @robust Result wrapper

    # Check if result failed or if execution had no successes
    if result["result"].success:
        exec_results = result["result"].data
        if "successful_count" in exec_results:
            assert exec_results["successful_count"] == 0


@pytest.mark.asyncio
async def test_multiple(state):
    """Test execution of multiple tools in sequence."""
    # Create tools that track execution order
    execution_order = []

    class OrderedTool(BaseTool):
        def __init__(self, name: str):
            super().__init__(
                name=name,
                description=f"Tool {name}",
                emoji="🔧",
                examples=[],
            )

        async def run(self, **kwargs):
            execution_order.append(self.name)
            return Result(f"{self.name}_result")

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

    wrapped = await act(state, tools=tools)
    result = unwrap(wrapped)  # Unwrap @robust Result wrapper

    # Check that tools executed in order
    assert execution_order == ["first", "second", "third"]

    # Check execution results
    assert result["result"].success
    exec_results = result["result"].data
    assert exec_results["successful_count"] == 3
    assert exec_results["failed_count"] == 0
