"""Flow routing tests - core business logic."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.context import Context
from cogency.flow import Flow, _route_from_act, _route_from_preprocess, _route_from_reason
from cogency.output import Output
from cogency.state import State


@pytest.fixture
def mock_llm():
    return Mock()


@pytest.fixture
def mock_tools():
    return Mock()


@pytest.fixture
def mock_memory():
    return Mock()


@pytest.fixture
def flow(mock_llm, mock_tools, mock_memory):
    return Flow(llm=mock_llm, tools=mock_tools, memory=mock_memory)


def test_init_defaults(mock_llm, mock_tools):
    flow = Flow(llm=mock_llm, tools=mock_tools, memory=None)
    assert flow.llm is mock_llm
    assert flow.tools is mock_tools
    assert flow.memory is None
    assert flow.identity is None
    assert flow.json_schema is None
    assert flow.system_prompt is None


def test_init(mock_llm, mock_tools, mock_memory):
    routing = {
        "entry_point": "preprocess",
        "edges": {
            "preprocess": {"type": "conditional", "condition": "_route_from_preprocess"},
            "reason": {"type": "conditional", "condition": "_route_from_reason"},
            "act": {"type": "conditional", "condition": "_route_from_act"},
            "respond": {"type": "end"},
        },
    }
    flow = Flow(
        llm=mock_llm,
        tools=mock_tools,
        memory=mock_memory,
        routing_table=routing,
        identity="test-agent",
        json_schema="{}",
        system_prompt="test prompt",
    )
    assert flow.routing_table == routing
    assert flow.identity == "test-agent"
    assert flow.json_schema == "{}"
    assert flow.system_prompt == "test prompt"


@pytest.mark.asyncio
async def test_preprocess_no_tools():
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow["selected_tools"] = []
    result = await _route_from_preprocess(state)
    assert result == "respond"


@pytest.mark.asyncio
async def test_preprocess_with_tools():
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow["selected_tools"] = ["tool1", "tool2"]
    result = await _route_from_preprocess(state)
    assert result == "reason"


@pytest.mark.asyncio
async def test_reason_no_calls():
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow["tool_calls"] = []
    result = await _route_from_reason(state)
    assert result == "respond"


@pytest.mark.asyncio
async def test_reason_with_calls():
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow["tool_calls"] = [{"name": "test"}]
    result = await _route_from_reason(state)
    assert result == "act"


@pytest.mark.asyncio
async def test_act_max_iterations():
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow.update(
        {
            "execution_results": Mock(success=True),
            "iteration": 5,
            "MAX_ITERATIONS": 5,
            "stop_reason": None,
            "tool_failures": 0,
            "quality_retries": 0,
        }
    )
    result = await _route_from_act(state)
    assert result == "respond"
    assert state["stop_reason"] == "max_iterations_reached"


@pytest.mark.asyncio
async def test_act_stop_reason():
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow.update(
        {
            "execution_results": Mock(success=True),
            "iteration": 1,
            "MAX_ITERATIONS": 5,
            "stop_reason": "max_iterations_reached",
            "tool_failures": 0,
            "quality_retries": 0,
        }
    )
    result = await _route_from_act(state)
    assert result == "respond"


@pytest.mark.asyncio
async def test_act_failed():
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow.update(
        {
            "execution_results": Mock(success=False),
            "iteration": 1,
            "MAX_ITERATIONS": 5,
            "stop_reason": None,
            "tool_failures": 2,
            "quality_retries": 0,
        }
    )
    result = await _route_from_act(state)
    assert result == "reason"
    assert state["tool_failures"] == 3


@pytest.mark.asyncio
async def test_act_max_failures():
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow.update(
        {
            "execution_results": Mock(success=False),
            "iteration": 1,
            "MAX_ITERATIONS": 5,
            "stop_reason": None,
            "tool_failures": 3,
            "quality_retries": 0,
        }
    )
    result = await _route_from_act(state)
    assert result == "respond"
    assert state["stop_reason"] == "repeated_tool_failures"


@pytest.mark.asyncio
@patch("cogency.nodes.reasoning.adaptive.assess_tools")
async def test_act_poor_quality(mock_assess):
    mock_assess.return_value = "poor"
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow.update(
        {
            "execution_results": Mock(success=True),
            "iteration": 1,
            "MAX_ITERATIONS": 5,
            "stop_reason": None,
            "tool_failures": 0,
            "quality_retries": 0,
        }
    )
    result = await _route_from_act(state)
    assert result == "reason"
    assert state["quality_retries"] == 1


@pytest.mark.asyncio
@patch("cogency.nodes.reasoning.adaptive.assess_tools")
async def test_act_max_quality(mock_assess):
    mock_assess.return_value = "poor"
    context = Context("test query")
    state = State(context=context, query="test query")
    state.flow.update(
        {
            "execution_results": Mock(success=True),
            "iteration": 1,
            "MAX_ITERATIONS": 5,
            "stop_reason": None,
            "tool_failures": 0,
            "quality_retries": 2,
        }
    )
    result = await _route_from_act(state)
    assert result == "reason"
