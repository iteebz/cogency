import pytest
import json
from unittest.mock import Mock
from cogency.router import Router
from cogency.types import AgentState, ExecutionTrace
from cogency.constants import NodeName


@pytest.fixture
def mock_trace():
    return ExecutionTrace()

@pytest.fixture
def mock_tools():
    mock_tool1 = Mock()
    mock_tool1.name = "tool1"
    mock_tool1.description = "description of tool1"
    mock_tool2 = Mock()
    mock_tool2.name = "tool2"
    mock_tool2.description = "description of tool2"
    return [mock_tool1, mock_tool2]

@pytest.fixture
def router(mock_tools):
    return Router(tools=mock_tools)

def create_agent_state(trace, last_node_output=None, thinking_response=None, skip_thinking=False):
    state = AgentState(
        context=Mock(),
        trace=trace,
        query="test query"
    )
    if last_node_output is not None:
        state["last_node_output"] = last_node_output
    if thinking_response is not None:
        state["thinking_response"] = thinking_response
    if skip_thinking:
        state["skip_thinking"] = True
    return state


class TestRouter:

    async def test_route_from_think_skip_thinking(self, router, mock_trace):
        state = create_agent_state(mock_trace, thinking_response={"decision": "direct_response"}, skip_thinking=True)
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "skip_thinking is true" in mock_trace.entries[-1]["message"]

    async def test_route_from_think_need_tools(self, router, mock_trace):
        thinking_response = {"decision": "need_tools", "reasoning": "I need a tool to find information.", "tools": "tool1"}
        state = create_agent_state(mock_trace, thinking_response=thinking_response, last_node_output=json.dumps(thinking_response))
        next_node = router.route(state)
        assert next_node == NodeName.PLAN.value
        assert "thinking output indicates tools needed" in mock_trace.entries[-1]["message"]

    async def test_route_from_think_direct_response(self, router, mock_trace):
        thinking_response = {"decision": "direct_response", "reasoning": "I can answer directly."}
        state = create_agent_state(mock_trace, thinking_response=thinking_response, last_node_output=json.dumps(thinking_response))
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "no tools needed" in mock_trace.entries[-1]["message"]

    async def test_route_from_think_unrecognized_decision(self, router, mock_trace):
        thinking_response = {"decision": "unrecognized", "reasoning": "unknown"}
        state = create_agent_state(mock_trace, thinking_response=thinking_response, last_node_output=json.dumps(thinking_response))
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "Warning: Thinking decision not recognized" in mock_trace.entries[-1]["message"]

    async def test_route_from_plan_tool_needed(self, router, mock_trace):
        plan_output = {"action": "tool_needed", "tool_call": {"name": "tool1", "args": {"arg": "value"}}}
        state = create_agent_state(mock_trace, last_node_output=json.dumps(plan_output))
        next_node = router.route(state)
        assert next_node == NodeName.ACT.value
        assert "plan indicates tool needed" in mock_trace.entries[-1]["message"]

    async def test_route_from_plan_direct_response(self, router, mock_trace):
        plan_output = {"action": "direct_response", "answer": "Here is your answer."}
        state = create_agent_state(mock_trace, last_node_output=json.dumps(plan_output))
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "plan indicates direct response" in mock_trace.entries[-1]["message"]

    async def test_route_from_plan_unrecognized_action(self, router, mock_trace):
        plan_output = {"action": "unrecognized", "answer": "Here is your answer."}
        state = create_agent_state(mock_trace, last_node_output=json.dumps(plan_output))
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "Warning: Plan parsing failed or action not recognized" in mock_trace.entries[-1]["message"]

    async def test_route_from_plan_malformed_json(self, router, mock_trace):
        state = create_agent_state(mock_trace, last_node_output="this is not json")
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "default fallback to RESPOND" in mock_trace.entries[-1]["message"]

    async def test_route_from_reflect_continue(self, router, mock_trace):
        reflect_output = {"status": "continue", "missing": "more info", "reasoning": "need more data"}
        state = create_agent_state(mock_trace, last_node_output=json.dumps(reflect_output))
        next_node = router.route(state)
        assert next_node == NodeName.PLAN.value
        assert "reflection indicates continue" in mock_trace.entries[-1]["message"]

    async def test_route_from_reflect_complete(self, router, mock_trace):
        reflect_output = {"status": "complete", "reasoning": "task done"}
        state = create_agent_state(mock_trace, last_node_output=json.dumps(reflect_output))
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "reflection indicates complete" in mock_trace.entries[-1]["message"]

    async def test_route_from_reflect_unrecognized_status(self, router, mock_trace):
        reflect_output = {"status": "unrecognized", "reasoning": "unknown"}
        state = create_agent_state(mock_trace, last_node_output=json.dumps(reflect_output))
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "Warning: Reflect parsing failed or status not recognized" in mock_trace.entries[-1]["message"]

    async def test_route_from_reflect_malformed_json(self, router, mock_trace):
        state = create_agent_state(mock_trace, last_node_output="this is not json")
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "default fallback to RESPOND" in mock_trace.entries[-1]["message"]

    async def test_route_default_fallback(self, router, mock_trace):
        state = create_agent_state(mock_trace, last_node_output="some random text")
        next_node = router.route(state)
        assert next_node == NodeName.RESPOND.value
        assert "default fallback to RESPOND" in mock_trace.entries[-1]["message"]
