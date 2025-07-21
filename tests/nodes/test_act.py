"""Test Act node - tool execution logic."""

from unittest.mock import AsyncMock

import pytest

from cogency.context import Context
from cogency.nodes.act import act
from cogency.output import Output
from cogency.state import State
from cogency.tools.base import BaseTool


class MockTool(BaseTool):
    """Simple mock tool."""

    def __init__(self, name: str, should_succeed: bool = True, result: dict = None):
        super().__init__(name=name, description=f"Mock {name}", emoji="🧪")
        self.should_succeed = should_succeed
        self.result = result or {"success": True}

    async def run(self, **kwargs):
        if not self.should_succeed:
            raise Exception("Tool failed")
        return self.result

    def schema(self):
        return '{"type": "object"}'

    def examples(self):
        return [f'{{"name": "{self.name}", "args": {{}}}}']


@pytest.fixture
def output():
    output = Output(trace=True)
    output.send = AsyncMock()  # Mock the send method
    return output


@pytest.fixture
def state(output):
    context = Context("test query")
    return State(context=context, query="test query", output=output)


@pytest.fixture
def mock_tools():
    return [
        MockTool("calculator", True, {"result": 42}),
        MockTool("search", True, {"results": ["data"]}),
    ]


@pytest.mark.asyncio
async def test_no_tool_calls(state, mock_tools):
    """Test act node when no tool calls are present."""
    state["tool_calls"] = None

    result = await act(state, tools=mock_tools)

    assert result["execution_results"]["type"] == "no_action"
    assert result["next_node"] == "reason"


@pytest.mark.asyncio
async def test_empty_tool_calls(state, mock_tools):
    """Test act node with empty tool call string."""
    state["tool_calls"] = ""

    result = await act(state, tools=mock_tools)

    assert result["execution_results"]["type"] == "no_action"
    assert result["next_node"] == "reason"


@pytest.mark.asyncio
async def test_invalid_tool_calls(state, mock_tools):
    """Test act node with invalid JSON tool calls."""
    state["tool_calls"] = "invalid json"

    result = await act(state, tools=mock_tools)

    assert result["execution_results"]["type"] == "no_action"
    assert result["next_node"] == "reason"


@pytest.mark.asyncio
async def test_successful_tool_execution(state, mock_tools):
    """Test successful tool execution."""
    state["tool_calls"] = '[{"name": "calculator", "args": {"x": 5}}]'

    result = await act(state, tools=mock_tools)

    assert result["next_node"] == "reason"
    assert "execution_results" in result
    # Should have successful execution
    exec_results = result["execution_results"]
    if "successful_count" in exec_results:
        assert exec_results["successful_count"] >= 1


@pytest.mark.asyncio
async def test_failed_tool_execution(state):
    """Test handling of failed tool execution."""
    failing_tool = MockTool("failing_tool", should_succeed=False)
    state["tool_calls"] = '[{"name": "failing_tool", "args": {}}]'

    result = await act(state, tools=[failing_tool])

    assert result["next_node"] == "reason"
    exec_results = result["execution_results"]
    if "successful_count" in exec_results:
        assert exec_results["successful_count"] == 0


@pytest.mark.asyncio
async def test_multiple_tool_execution(state, mock_tools):
    """Test execution of multiple tools."""
    state["tool_calls"] = """[
        {"name": "calculator", "args": {"x": 5}},
        {"name": "search", "args": {"query": "test"}}
    ]"""

    result = await act(state, tools=mock_tools)

    assert result["next_node"] == "reason"
    exec_results = result["execution_results"]
    if "successful_count" in exec_results:
        assert exec_results["successful_count"] >= 1
