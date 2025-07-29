"""Phase integration tests - testing actual Cogency architecture."""

from unittest.mock import AsyncMock

import pytest
from resilient_result import Result

from cogency.phases.act import act
from cogency.phases.reason import reason
from cogency.phases.respond import respond
from cogency.state import State
from cogency.tools.calculator import Calculator
from tests.conftest import MockLLM


@pytest.fixture
def state():
    """Basic state for testing."""
    return State(query="What is 2 + 2?")


@pytest.mark.asyncio
async def test_reason_phase_direct_answer(state):
    """Test reason phase when it can answer directly."""
    llm = MockLLM()
    llm.run = AsyncMock(
        return_value=Result.ok('{"reasoning": "I can answer this directly: 2 + 2 = 4"}')
    )

    await reason(state, llm=llm, tools=[])

    # Should have no tool calls for direct answer
    assert not state.tool_calls
    # No action added for direct answers (correct behavior)
    assert len(state.actions) == 0


@pytest.mark.asyncio
async def test_reason_phase_needs_tools(state):
    """Test reason phase when it needs tools."""
    llm = MockLLM()
    llm.run = AsyncMock(
        return_value=Result.ok(
            '{"reasoning": "I need to calculate this.", "tool_calls": [{"name": "calculator", "args": {"expression": "2 + 2"}}]}'
        )
    )

    await reason(state, llm=llm, tools=[Calculator()])

    # Should have tool calls
    assert state.tool_calls
    assert len(state.tool_calls) == 1
    assert state.tool_calls[0].name == "calculator"


@pytest.mark.asyncio
async def test_act_phase_execution(state):
    """Test act phase actually executes tools."""
    # Setup state with tool calls and add action first
    state.tool_calls = [{"name": "calculator", "args": {"expression": "2 + 2"}}]
    state.add_action(
        mode="fast",
        thinking="Need to calculate",
        planning="Use calculator",
        reflection="",
        approach="calculate",
        tool_calls=state.tool_calls,
    )

    tools = [Calculator()]
    await act(state, tools=tools)

    # Should have results (tool calls with outcome key)
    results = state.get_latest_results()
    assert len(results) > 0
    assert results[0]["outcome"] == "success"
    assert "4" in str(results[0]["result"])


@pytest.mark.asyncio
async def test_respond_phase_formats_response(state):
    """Test respond phase creates final response."""
    llm = MockLLM()

    await respond(state, llm=llm, tools=[])

    # Should have a response
    assert state.response is not None


@pytest.mark.asyncio
async def test_complete_reasoning_cycle(state):
    """Test full reasoning cycle: reason -> act -> reason -> respond."""
    tools = [Calculator()]
    llm = MockLLM()

    # 1. First reason (needs tools) - this adds an action
    llm.run = AsyncMock(
        return_value=Result.ok(
            '{"reasoning": "I need to calculate 2 + 2.", "tool_calls": [{"name": "calculator", "args": {"expression": "2 + 2"}}]}'
        )
    )
    await reason(state, llm=llm, tools=tools)
    assert state.tool_calls
    assert len(state.actions) > 0  # reason() should have added an action

    # 2. Act (execute tools)
    await act(state, tools=tools)
    results = state.get_latest_results()
    assert len(results) > 0

    # 3. Second reason (reflect on results)
    llm.run = AsyncMock(
        return_value=Result.ok(
            '{"reasoning": "The calculator shows 2 + 2 = 4. I can now respond."}'
        )
    )
    await reason(state, llm=llm, tools=tools)

    # 4. Respond (final answer)
    await respond(state, llm=llm, tools=[])
    assert state.response


@pytest.mark.asyncio
async def test_simple_no_tools_flow(state):
    """Test simple question that needs no tools."""
    state.query = "Hello, how are you?"
    llm = MockLLM()
    llm.run = AsyncMock(
        return_value=Result.ok('{"reasoning": "This is a greeting, I can respond directly."}')
    )

    # 1. Reason (no tools needed)
    await reason(state, llm=llm, tools=[])
    assert not state.tool_calls

    # 2. Respond directly
    await respond(state, llm=llm, tools=[])
    assert state.response
