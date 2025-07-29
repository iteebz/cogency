"""Core phase tests - essential business logic only."""

from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency.phases.act import act
from cogency.phases.respond import respond
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.executor import execute_single_tool
from cogency.types.tools import ToolOutcome
from cogency.utils.parsing import parse_tool_calls


class MockTool(BaseTool):
    def __init__(self, name: str = "test_tool", should_fail: bool = False):
        super().__init__(
            name=name,
            description=f"Mock tool: {name}",
            examples=[f'{{"name": "{name}", "args": {{"test": "value"}}}}'],
            rules=[],
        )
        self.should_fail = should_fail

    async def run(self, **kwargs):
        if self.should_fail:
            raise Exception("Tool execution failed")
        return Result.ok(f"success from {self.name}")

    def format_human(self, params, results=None):
        return f"({self.name})", str(results) if results else ""

    def format_agent(self, result_data: dict[str, any]) -> str:
        return f"Tool output: {result_data}"


def test_tool_call_parsing():
    """Test basic tool call parsing."""
    from cogency.utils.parsing import parse_json

    llm_response = '{"tool_calls": [{"name": "calculator", "args": {"x": 5}}]}'
    parse_result = parse_json(llm_response)
    assert parse_result.success
    json_data = parse_result.data
    result = parse_tool_calls(json_data)
    assert len(result) == 1
    assert result[0]["name"] == "calculator"

    # Handle malformed JSON
    parse_result = parse_json("invalid json")
    assert not parse_result.success
    # parse_tool_calls should not be called with invalid data, but if it is, it should return None
    assert parse_tool_calls(parse_result.data) is None

    no_calls_json_result = parse_json('{"no_tools": true}')
    assert no_calls_json_result.success
    assert parse_tool_calls(no_calls_json_result.data) is None

    # Test with empty tool_calls list
    empty_calls_json_result = parse_json('{"tool_calls": []}')
    assert empty_calls_json_result.success
    assert parse_tool_calls(empty_calls_json_result.data) == []


@pytest.mark.asyncio
async def test_tool_execution_errors():
    """Test tool execution error handling."""
    failing_tool = MockTool("fail", should_fail=True)
    working_tool = MockTool("work", should_fail=False)
    tools = [failing_tool, working_tool]

    # Test failure
    name, args, result = await execute_single_tool("fail", {}, tools)
    assert not result.success
    assert result.error is not None

    # Test success
    name, args, result = await execute_single_tool("work", {}, tools)
    assert result.success

    # Test missing tool
    with pytest.raises(ValueError):
        await execute_single_tool("missing", {}, tools)


@pytest.mark.asyncio
async def test_respond_phase_output():
    """Test respond phase produces conversational text only."""
    mock_llm = AsyncMock()

    async def mock_stream(*args, **kwargs):
        yield "The weather is sunny today!"

    async def mock_run(*args, **kwargs):
        from resilient_result import Result

        return Result.ok("The weather is sunny today!")

    mock_llm.stream = mock_stream
    mock_llm.run = mock_run

    state = State(query="weather?", messages=[], user_id="test")

    await respond(state, llm=mock_llm, tools=[])

    assert isinstance(state.response, str)
    assert not state.response.startswith("{")
    # The respond function doesn't set stop_reason to "finished"


@pytest.mark.asyncio
async def test_act_routing():
    """Test act phase routing behavior."""
    from cogency.types.tools import ToolCall

    tool = MockTool("test_tool")
    state = State(query="test", messages=[], user_id="test")

    # Create proper ToolCall objects
    tool_calls = [ToolCall(name="test_tool", args={})]
    state.tool_calls = tool_calls

    # Add action first (required by act phase)
    state.add_action(
        mode="fast",
        thinking="test thinking",
        planning="test planning",
        reflection="test reflection",
        approach="test approach",
        tool_calls=tool_calls,
    )

    await act(state, tools=[tool])
    latest_results = state.latest_tool_results
    assert len(latest_results) > 0
    assert latest_results[0].success

    # Test no tool calls
    state.tool_calls = []
    await act(state, tools=[])
    # Should not change existing results
    assert len(state.latest_tool_results) > 0  # Still has previous results
