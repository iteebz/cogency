"""Flow routing tests - core business logic."""

from unittest.mock import AsyncMock, Mock, patch

import pytest

from cogency.context import Context
from cogency.flow import Flow
from cogency.phases.act import Act
from cogency.phases.preprocess import Preprocess
from cogency.phases.reason import Reason
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
    assert flow.common_kwargs["llm"] is mock_llm
    assert flow.common_kwargs["tools"] is mock_tools
    assert flow.common_kwargs["identity"] is None
    assert flow.flow is not None


def test_init_with_params(mock_llm, mock_tools, mock_memory):
    flow = Flow(
        llm=mock_llm,
        tools=mock_tools,
        memory=mock_memory,
        identity="test-agent",
        json_schema="{}",
        system_prompt="test prompt",
    )
    assert flow.common_kwargs["llm"] is mock_llm
    assert flow.common_kwargs["tools"] is mock_tools
    assert flow.common_kwargs["identity"] == "test-agent"
    assert flow.common_kwargs["system_prompt"] == "test prompt"
    assert flow.flow is not None


def test_preprocess_routing_no_tools():
    node = Preprocess()
    state = State(context=Context("test"), query="test")
    state["selected_tools"] = []
    result = node.next_node(state)
    assert result == "respond"


def test_preprocess_routing_with_tools():
    node = Preprocess()
    state = State(context=Context("test"), query="test")
    state["selected_tools"] = ["tool1", "tool2"]
    result = node.next_node(state)
    assert result == "reason"


def test_reason_routing_no_calls():
    node = Reason()
    state = State(context=Context("test"), query="test")
    state["tool_calls"] = []
    result = node.next_node(state)
    assert result == "respond"


def test_reason_routing_with_calls():
    node = Reason()
    state = State(context=Context("test"), query="test")
    state["tool_calls"] = [{"name": "test"}]
    result = node.next_node(state)
    assert result == "act"


@patch("cogency.phases.reasoning.adaptive.assess_tools")
def test_act_routing_max_iterations(mock_assess):
    mock_assess.return_value = "good"
    node = Act()
    state = State(context=Context("test"), query="test")
    state["result"] = Mock(success=True)
    state["iteration"] = 15  # Greater than default max_iterations (12)
    state["stop_reason"] = None
    state["tool_failures"] = 0
    state["quality_retries"] = 0

    result = node.next_node(state)
    assert result == "respond"
    assert state["stop_reason"] == "max_iterations_reached"


def test_act_routing_stop_reason():
    node = Act()
    state = State(context=Context("test"), query="test")
    state["result"] = Mock(success=True)
    state["iteration"] = 1
    state["max_iterations"] = 5
    state["stop_reason"] = "max_iterations_reached"
    state["tool_failures"] = 0
    state["quality_retries"] = 0

    result = node.next_node(state)
    assert result == "respond"


def test_act_routing_failed():
    node = Act()
    state = State(context=Context("test"), query="test")
    state["result"] = Mock(success=False)
    state["iteration"] = 1
    state["max_iterations"] = 5
    state["stop_reason"] = None
    state["tool_failures"] = 2
    state["quality_retries"] = 0

    result = node.next_node(state)
    assert result == "reason"
    assert state["tool_failures"] == 3


def test_act_routing_max_failures():
    node = Act()
    state = State(context=Context("test"), query="test")
    state["result"] = Mock(success=False)
    state["iteration"] = 1
    state["max_iterations"] = 5
    state["stop_reason"] = None
    state["tool_failures"] = 3
    state["quality_retries"] = 0

    result = node.next_node(state)
    assert result == "respond"
    assert state["stop_reason"] == "repeated_tool_failures"


@patch("cogency.phases.reasoning.adaptive.assess_tools")
def test_act_routing_poor_quality(mock_assess):
    mock_assess.return_value = "poor"
    node = Act()
    state = State(context=Context("test"), query="test")
    state["result"] = Mock(success=True)
    state["iteration"] = 1
    state["max_iterations"] = 5
    state["stop_reason"] = None
    state["tool_failures"] = 0
    state["quality_retries"] = 0

    result = node.next_node(state)
    assert result == "reason"
    assert state["quality_retries"] == 1
