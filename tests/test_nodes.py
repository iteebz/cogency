"""Core node tests - essential business logic only."""
import pytest
from unittest.mock import AsyncMock, Mock

from cogency.tools.executor import parse_tool_calls, execute_single_tool
from cogency.tools.result import is_success
from cogency.utils.parsing import parse_json
from cogency.nodes.respond import respond
from cogency.nodes.act import act
from cogency.state import State
from cogency.context import Context
from cogency.output import Output
from cogency.tools.base import BaseTool


class MockTool(BaseTool):
    def __init__(self, name: str = "test_tool", should_fail: bool = False):
        super().__init__(name, f"Mock tool: {name}")
        self.should_fail = should_fail
    
    async def run(self, **kwargs):
        if self.should_fail:
            raise Exception("Tool execution failed")
        return {"result": f"success from {self.name}"}
    
    def schema(self):
        return "test tool schema"
    
    def examples(self):
        return [f'{{"name": "{self.name}", "args": {{"test": "value"}}}}']


def test_tool_call_parsing():
    """Test basic tool call parsing."""
    llm_response = '{"tool_calls": [{"name": "calculator", "args": {"x": 5}}]}'
    result = parse_tool_calls(llm_response)
    assert len(result) == 1
    assert result[0]["name"] == "calculator"
    
    # Handle malformed JSON
    assert parse_tool_calls("invalid json") is None
    assert parse_tool_calls("no tool calls") is None


@pytest.mark.asyncio
async def test_tool_execution_errors():
    """Test tool execution error handling."""
    failing_tool = MockTool("fail", should_fail=True)
    working_tool = MockTool("work", should_fail=False)
    tools = [failing_tool, working_tool]
    
    # Test failure
    name, args, result = await execute_single_tool("fail", {}, tools)
    assert "error" in result
    assert not is_success(result)
    
    # Test success
    name, args, result = await execute_single_tool("work", {}, tools)
    assert is_success(result)
    
    # Test missing tool
    with pytest.raises(ValueError):
        await execute_single_tool("missing", {}, tools)


@pytest.mark.asyncio
async def test_respond_node_output():
    """Test respond node produces conversational text only."""
    mock_llm = AsyncMock()
    async def mock_stream(*args, **kwargs):
        yield "The weather is sunny today!"
    mock_llm.stream = mock_stream
    
    context = Context(query="weather?", messages=[], user_id="test")
    state = State(context=context, query="test", output=Output())
    
    result_state = await respond(state, llm=mock_llm)
    
    assert isinstance(result_state["final_response"], str)
    assert not result_state["final_response"].startswith("{")
    assert result_state["next_node"] == "END"


@pytest.mark.asyncio
async def test_act_node_routing():
    """Test act node routing behavior."""
    tool = MockTool("test_tool")
    context = Context(query="test", messages=[], user_id="test")
    state = State(context=context, query="test", output=Output())
    state["tool_calls"] = '[{"name": "test_tool", "args": {}}]'
    
    result = await act(state, tools=[tool])
    assert result["next_node"] == "reason"
    assert "execution_results" in result
    
    # Test no tool calls
    state["tool_calls"] = None
    result = await act(state, tools=[])
    assert result["next_node"] == "reason"
    assert result["execution_results"]["type"] == "no_action"
