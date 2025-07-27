"""Flow integration tests."""

from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency.context import Context
from cogency.flow import Flow
from cogency.nodes.act import act
from cogency.nodes.reason import reason
from cogency.nodes.respond import respond
from cogency.state import State
from cogency.tools.calculator import Calculator
from tests.conftest import MockLLM


@pytest.fixture
def basic_state():
    """Basic test state."""
    ctx = Context("Hello")
    return State(context=ctx, query="Hello")


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
async def test_direct_answer(basic_state):
    """Test reason node when direct answer possible."""
    llm = MockLLM()
    llm.run = AsyncMock(return_value=Result(data='{"reasoning": "I can answer directly."}'))

    await reason(basic_state, llm=llm, tools=[])
    assert not basic_state["tool_calls"]


@pytest.mark.asyncio
async def test_needs_tools(basic_state):
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
async def test_executes_tools(basic_state):
    """Test act node executes tool calls."""
    from resilient_result import Result

    from cogency.tools.base import BaseTool

    class MockTool(BaseTool):
        def __init__(self):
            super().__init__(name="mock_tool", description="Mock", emoji="🔧", examples=[])

        async def run(self, **kwargs):
            return Result("mock_result")

        def format_agent(self, **kwargs):
            return f"mock_tool({kwargs})"

        def format_human(self, params, results=None):
            return f"Mock params: {params}", f"Mock result: {results}"

    tools = [MockTool()]
    basic_state["tool_calls"] = [{"name": "mock_tool", "args": {"param": "value"}}]
    basic_state["selected_tools"] = tools

    from cogency.nodes.act import Act

    act_node = Act(tools=tools)
    state = await act_node(basic_state)
    result_data = state.result
    assert result_data.success


@pytest.mark.asyncio
async def test_formats_response(basic_state):
    """Test respond node formats final response."""
    llm = MockLLM()
    from cogency.nodes.respond import Respond

    respond_node = Respond(llm=llm, tools=[])
    state = await respond_node(basic_state)
    assert "final_response" in state
    assert state["final_response"]


@pytest.mark.asyncio
async def test_complete_node_flow(basic_state):
    """Test complete node-by-node flow: reason -> act -> reason -> respond."""
    from unittest.mock import AsyncMock

    from resilient_result import Result

    from cogency.nodes.act import Act
    from cogency.nodes.reason import Reason
    from cogency.nodes.respond import Respond
    from cogency.tools.base import BaseTool

    class MockTool(BaseTool):
        def __init__(self):
            super().__init__(name="mock_tool", description="Mock", emoji="🔧", examples=[])

        async def run(self, **kwargs):
            return Result("mock_result")

        def format_agent(self, **kwargs):
            return f"mock_tool({kwargs})"

        def format_human(self, params, results=None):
            return f"Mock params: {params}", f"Mock result: {results}"

    tools = [MockTool()]
    mock_llm = MockLLM()

    # 1. Reason (needs tools)
    mock_llm.run = AsyncMock(
        return_value=Result.ok(
            '{"reasoning": "I need the mock tool.", "tool_calls": [{"name": "mock_tool", "args": {"param": "test"}}]}'
        )
    )
    reason_node = Reason(llm=mock_llm, tools=tools)
    state = await reason_node(basic_state)

    # 2. Act
    state["selected_tools"] = tools
    act_node = Act(tools=tools)
    state = await act_node(state)
    result_data = state.result
    assert result_data.success

    # 3. Reason (reflect on results)
    mock_llm.run = AsyncMock(
        return_value=Result.ok('{"reasoning": "Got the result, now I can answer."}')
    )
    reason_node2 = Reason(llm=mock_llm, tools=tools)
    state = await reason_node2(state)

    # 4. Respond
    respond_node = Respond(llm=mock_llm, tools=[])
    final_state = await respond_node(state)
    assert "final_response" in final_state


@pytest.mark.asyncio
async def test_simple_reason_respond_flow(basic_state):
    """Test simple reason -> respond flow without tools."""
    from unittest.mock import AsyncMock

    from cogency.nodes.reason import Reason
    from cogency.nodes.respond import Respond

    mock_llm = MockLLM()
    mock_llm.run = AsyncMock(return_value=Result(data='{"reasoning": "Simple greeting."}'))

    # 1. Reason
    reason_node = Reason(llm=mock_llm, tools=[])
    state = await reason_node(basic_state)

    # 2. Respond
    respond_node = Respond(llm=mock_llm, tools=[])
    final_state = await respond_node(state)
    assert "final_response" in final_state
