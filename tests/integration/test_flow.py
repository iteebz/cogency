"""Flow integration tests."""

from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency.context import Context
from cogency.flow import Flow
from cogency.nodes.act import act
from cogency.nodes.reason import reason
from cogency.nodes.respond import respond
from cogency.output import Output
from cogency.state import State
from cogency.tools.calculator import Calculator
from tests.conftest import MockLLM


@pytest.fixture
def basic_state():
    """Basic test state."""
    ctx = Context("Hello")
    return State(context=ctx, query="Hello", output=Output())


@pytest.mark.asyncio
async def test_direct_flow():
    """Test simple preprocess -> respond flow."""
    llm = MockLLM()
    flow = Flow(llm=llm, tools=[], memory=None)
    assert flow.flow is not None


@pytest.mark.asyncio
async def test_tool_flow():
    """Test preprocess -> reason -> act -> reason -> respond flow."""
    llm = MockLLM()
    tools = [Calculator()]
    flow = Flow(llm=llm, tools=tools, memory=None)

    assert len(flow.tools) == 1
    assert flow.flow is not None


@pytest.mark.asyncio
async def test_reason_direct_answer(basic_state):
    """Test reason node when direct answer possible."""
    llm = MockLLM()
    llm.run = AsyncMock(return_value=Result(data='{"reasoning": "I can answer directly."}'))

    await reason(basic_state, llm=llm, tools=[])
    assert "tool_calls" not in basic_state.flow or not basic_state.flow["tool_calls"]


@pytest.mark.asyncio
async def test_reason_needs_tools(basic_state):
    """Test reason node when tools needed."""
    llm = MockLLM()
    llm.run = AsyncMock(
        return_value=Result(
            data='{"thinking": "Need tool.", "tool_calls": [{"name": "mock_tool", "args": {"param": "value"}}]}'
        )
    )

    await reason(basic_state, llm=llm, tools=[])
    assert basic_state.get("tool_calls") is not None


@pytest.mark.asyncio
async def test_act_executes_tools(basic_state):
    """Test act node executes tool calls."""
    from cogency.tools.base import BaseTool
    from cogency.utils.results import ToolResult

    class MockTool(BaseTool):
        def __init__(self):
            super().__init__(
                name="mock_tool", description="Mock", emoji="🔧", schema="", examples=[]
            )

        async def run(self, **kwargs):
            return ToolResult("mock_result")

        def format_agent(self, **kwargs):
            return f"mock_tool({kwargs})"

        def format_human(self, result):
            return f"Mock result: {result}"

    tools = [MockTool()]
    basic_state.flow["tool_calls"] = [{"name": "mock_tool", "args": {"param": "value"}}]
    basic_state.flow["selected_tools"] = tools

    result = await act(basic_state, tools=tools)
    action_result = result.action_result
    assert action_result.success


@pytest.mark.asyncio
async def test_respond_formats_response(basic_state):
    """Test respond node formats final response."""
    llm = MockLLM()
    result = await respond(basic_state, llm=llm, tools=[])

    assert "final_response" in result
    assert result["final_response"]
