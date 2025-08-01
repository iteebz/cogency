"""Comprehensive phase tests - integration and unit testing."""

from unittest.mock import AsyncMock, Mock

import pytest
from resilient_result import Result

from cogency.state import State
from cogency.steps.act import act
from cogency.steps.act.executor import execute_single_tool
from cogency.steps.reason import reason
from cogency.steps.respond import respond
from cogency.tools.base import Tool
from cogency.tools.code import Code
from cogency.utils.parsing import parse_tool_calls
from tests.conftest import MockLLM


class MockTool(Tool):
    def __init__(self, name: str = "test_tool", should_fail: bool = False):
        super().__init__(
            name=name,
            description=f"Mock tool: {name}",
            examples=[f'{{"name": "{name}", "args": {{"test": "value"}}}}'],
            rules=[],
            schema={
                "type": "object",
                "properties": {"test": {"type": "string"}},
                "required": ["test"],
            },
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


@pytest.mark.asyncio
async def test_execution_errors():
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
async def test_respond_output():
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

    await respond(state, AsyncMock(), llm=mock_llm, tools=[])

    assert isinstance(state.response, str)
    assert not state.response.startswith("{")
    # The respond function doesn't set stop_reason to "finished"


@pytest.mark.asyncio
async def test_routing():
    """Test act phase routing behavior."""
    tool = MockTool("test_tool")
    state = State(query="test", messages=[], user_id="test")

    # Create proper ToolCall objects
    tool_calls = [{"name": "test_tool", "args": {}}]
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

    await act(state, AsyncMock(), tools=[tool])
    latest_results = state.latest_tool_results
    assert len(latest_results) > 0
    assert latest_results[0]["outcome"] == "success"

    # Test no tool calls
    state.tool_calls = []
    await act(state, AsyncMock(), tools=[])
    # Should not change existing results
    assert len(state.latest_tool_results) > 0  # Still has previous results


# Integration tests from test_phase_integration.py


@pytest.fixture
def state():
    """Basic state for testing."""
    return State(query="What is 2 + 2?")


@pytest.mark.asyncio
async def test_reason_direct(state):
    """Test reason phase when it can answer directly."""
    llm = MockLLM()
    llm.run = AsyncMock(
        return_value=Result.ok('{"reasoning": "I can answer this directly: 2 + 2 = 4"}')
    )

    await reason(state, AsyncMock(), llm=llm, tools=[], memory=None)

    # Should have no tool calls for direct answer
    assert not state.tool_calls
    # Action is always added when reasoning produces a response
    assert len(state.actions) == 1


@pytest.mark.asyncio
async def test_reason_tools(state):
    """Test reason phase when it needs tools."""
    llm = MockLLM()
    llm.run = AsyncMock(
        return_value=Result.ok(
            '{"reasoning": "I need to calculate this.", "tool_calls": [{"name": "code", "args": {"expression": "2 + 2"}}]}'
        )
    )

    await reason(state, AsyncMock(), llm=llm, tools=[Code()], memory=None)

    # Should have tool calls
    assert state.tool_calls
    assert len(state.tool_calls) == 1
    assert state.tool_calls[0]["name"] == "code"


@pytest.mark.asyncio
async def test_act_execution(state):
    """Test act phase actually executes tools."""
    # Setup state with tool calls and add action first
    state.tool_calls = [{"name": "code", "args": {"code": "2 + 2"}}]
    state.add_action(
        mode="fast",
        thinking="Need to calculate",
        planning="Use code tool",
        reflection="",
        approach="calculate",
        tool_calls=state.tool_calls,
    )

    tools = [Code()]
    await act(state, AsyncMock(), tools=tools)

    # Should have results (tool calls with outcome key)
    results = state.latest_results()
    assert len(results) > 0
    assert results[0]["outcome"] == "success"
    assert results[0]["result"]["success"] is True
    assert results[0]["result"]["exit_code"] == 0


@pytest.mark.asyncio
async def test_respond_formats(state):
    """Test respond phase creates final response."""
    llm = MockLLM()

    await respond(state, AsyncMock(), llm=llm, tools=[])

    # Should have a response
    assert state.response is not None


@pytest.mark.asyncio
async def test_full_cycle(state):
    """Test full reasoning cycle: reason -> act -> reason -> respond."""
    tools = [Code()]
    llm = MockLLM()

    # 1. First reason (needs tools) - this adds an action
    llm.run = AsyncMock(
        return_value=Result.ok(
            '{"reasoning": "I need to calculate 2 + 2.", "tool_calls": [{"name": "code", "args": {"code": "2 + 2"}}]}'
        )
    )
    await reason(state, AsyncMock(), llm=llm, tools=tools, memory=None)
    assert state.tool_calls
    assert len(state.actions) > 0  # reason() should have added an action

    # 2. Act (execute tools)
    await act(state, AsyncMock(), tools=tools)
    results = state.latest_results()
    assert len(results) > 0

    # 3. Second reason (reflect on results)
    llm.run = AsyncMock(
        return_value=Result.ok('{"reasoning": "The code tool shows 2 + 2 = 4. I can now respond."}')
    )
    await reason(state, AsyncMock(), llm=llm, tools=tools, memory=None)

    # 4. Respond (final answer)
    await respond(state, AsyncMock(), llm=llm, tools=[])
    assert state.response


@pytest.mark.asyncio
async def test_no_tools_flow(state):
    """Test simple question that needs no tools."""
    state.query = "Hello, how are you?"
    llm = MockLLM()
    llm.run = AsyncMock(
        return_value=Result.ok('{"reasoning": "This is a greeting, I can respond directly."}')
    )

    # 1. Reason (no tools needed)
    await reason(state, AsyncMock(), llm=llm, tools=[], memory=None)
    assert not state.tool_calls

    # 2. Respond directly
    await respond(state, AsyncMock(), llm=llm, tools=[])
    assert state.response
