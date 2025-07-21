"""Test end-to-end flow: preprocess → reason → act → respond."""
import pytest
from unittest.mock import AsyncMock

from cogency.nodes.reason import reason_node
from cogency.nodes.act import act_node
from cogency.nodes.respond import respond_node
from cogency import AgentState

@pytest.fixture
def agent_state(context): # Using the context fixture from conftest.py
    """Provides a basic AgentState for tests."""
    from cogency.output import OutputManager
    return AgentState(context=context, query="Hello", output=OutputManager())

class TestFlowNodes:
    """Test individual flow nodes with the new decoupled architecture."""
    
    @pytest.mark.asyncio
    async def test_reason_node_can_answer_directly(self, agent_state, mock_llm, tools):
        mock_llm.run = AsyncMock(return_value='{"reasoning": "I can answer this directly."}')
        
        result = await reason_node(agent_state, llm=mock_llm, tools=tools)
        
        assert result["next_node"] == "respond"
        assert "tool_calls" not in result or not result["tool_calls"]

    @pytest.mark.asyncio
    async def test_reason_node_needs_tools(self, agent_state, mock_llm, tools):
        mock_llm.run = AsyncMock(return_value='{"reasoning": "I need a tool.", "tool_calls": [{"name": "mock_tool", "args": {"param": "value"}}]}')
        
        result = await reason_node(agent_state, llm=mock_llm, tools=tools)
        
        assert result["next_node"] == "act"
        assert result["tool_calls"]

    @pytest.mark.asyncio
    async def test_act_node_executes_tools(self, agent_state, tools):
        # The state passed to act_node now comes from the output of reason_node
        state_from_reason = {
            "tool_calls": [{"name": "mock_tool", "args": {"param": "value"}}],
            "selected_tools": tools
        }
        # We need to merge this with the initial agent_state for the node to have context
        # Copy the agent_state
        full_state = agent_state
        # Add the state_from_reason items to the flow dict
        for key, value in state_from_reason.items():
            full_state.flow[key] = value

        result = await act_node(full_state, tools=tools)
        
        assert "execution_results" in result
        assert result["execution_results"]["success"]

    @pytest.mark.asyncio
    async def test_respond_node_formats_response(self, agent_state, mock_llm):
        # Respond node now gets a simple state, no complex reasoning decision needed
        result = await respond_node(agent_state, llm=mock_llm)
        
        assert "final_response" in result
        assert result["final_response"] # Should not be empty

class TestFlowIntegration:
    """Test complete flow integration by simulating the graph."""
    
    @pytest.mark.asyncio
    async def test_simple_direct_response_flow(self, agent_state, mock_llm, tools):
        mock_llm.run = AsyncMock(return_value='{"reasoning": "Simple greeting."}')
        
        # 1. Reason
        reason_result = await reason_node(agent_state, llm=mock_llm, tools=tools)
        assert reason_result["next_node"] == "respond"
        
        # 2. Respond
        # Update state with the result of the reason node
        current_state = agent_state
        # Copy specific keys we know are in the result
        if "next_node" in reason_result:
            current_state.flow["next_node"] = reason_result["next_node"]
        if "reasoning_response" in reason_result:
            current_state.flow["reasoning_response"] = reason_result["reasoning_response"]
        if "can_answer_directly" in reason_result:
            current_state.flow["can_answer_directly"] = reason_result["can_answer_directly"]
        if "tool_calls" in reason_result:
            current_state.flow["tool_calls"] = reason_result["tool_calls"]
        respond_result = await respond_node(current_state, llm=mock_llm)
        assert "final_response" in respond_result

    @pytest.mark.asyncio
    async def test_tool_usage_flow(self, agent_state, mock_llm, tools):
        # 1. Reason (needs tools)
        mock_llm.run = AsyncMock(return_value='{"reasoning": "I need the mock tool.", "tool_calls": [{"name": "mock_tool", "args": {"param": "test"}}]}')
        reason_result = await reason_node(agent_state, llm=mock_llm, tools=tools)
        assert reason_result["next_node"] == "act"

        # 2. Act
        state_for_act = agent_state
        # Copy specific keys we know are in the result
        if "next_node" in reason_result:
            state_for_act.flow["next_node"] = reason_result["next_node"]
        if "reasoning_response" in reason_result:
            state_for_act.flow["reasoning_response"] = reason_result["reasoning_response"]
        if "can_answer_directly" in reason_result:
            state_for_act.flow["can_answer_directly"] = reason_result["can_answer_directly"]
        if "tool_calls" in reason_result:
            state_for_act.flow["tool_calls"] = reason_result["tool_calls"]
        state_for_act.flow["selected_tools"] = tools
        state_for_act.flow["selected_tools"] = tools
        act_result = await act_node(state_for_act, tools=tools)
        assert act_result["execution_results"]["success"]

        # 3. Reason (reflect on results)
        mock_llm.run = AsyncMock(return_value='{"reasoning": "Got the result, now I can answer."}')
        state_for_reflection = agent_state
        # Add the act_result items to the flow dict
        for key in act_result.flow:
            state_for_reflection.flow[key] = act_result.flow[key]
        reflection_result = await reason_node(state_for_reflection, llm=mock_llm, tools=tools)
        assert reflection_result["next_node"] == "respond"

        # 4. Respond
        state_for_respond = agent_state
        # Add the reflection_result items to the flow dict
        for key in reflection_result.flow:
            state_for_respond.flow[key] = reflection_result.flow[key]
        respond_result = await respond_node(state_for_respond, llm=mock_llm)
        assert "final_response" in respond_result