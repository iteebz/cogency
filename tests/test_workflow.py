"""Test end-to-end workflow: preprocess → reason → act → respond."""
import pytest
from unittest.mock import AsyncMock, Mock

from cogency.nodes.reason import reason_node
from cogency.nodes.act import act_node
from cogency.nodes.respond import respond_node
from cogency.utils.parsing import extract_json_from_response, extract_tool_calls_from_json, extract_reasoning_text
from cogency.types import AgentState, ReasoningDecision


class TestWorkflowNodes:
    """Test individual workflow nodes."""
    
    @pytest.mark.asyncio
    async def test_reason_node_can_answer_directly(self, agent_state, mock_llm, tools):
        """Reason node should detect when it can answer directly."""
        # Mock LLM to return a direct response - no tool_calls means direct response
        mock_llm.invoke = AsyncMock(return_value="""
        {"reasoning": "I can answer this directly without tools."}
        """)
        
        result_state = await reason_node(
            agent_state,
            llm=mock_llm,
            tools=tools
        )
        
        assert result_state["can_answer_directly"] is True
        assert result_state["next_node"] == "respond"
        assert result_state["direct_response"] is None  # Reason node never sets direct_response
    
    @pytest.mark.asyncio
    async def test_reason_node_needs_tools(self, agent_state, mock_llm, tools):
        """Reason node should detect when tools are needed."""
        # Mock LLM to request tool usage - using new format with tool_calls array
        mock_llm.invoke = AsyncMock(return_value="""
        {"reasoning": "I need to use a tool first.", "tool_calls": [{"name": "mock_tool", "args": {"param": "value"}}]}
        """)
        
        result_state = await reason_node(
            agent_state,
            llm=mock_llm,
            tools=tools
        )
        
        assert result_state["can_answer_directly"] is False
        assert result_state["next_node"] == "act"
        assert result_state["tool_calls"] is not None
    
    @pytest.mark.asyncio
    async def test_act_node_executes_tools(self, agent_state, tools):
        """Act node should execute tool calls correctly."""
        # Set up state with tool calls
        agent_state["tool_calls"] = [{
            "name": "mock_tool",
            "args": {"param": "value"}
        }]
        
        result_state = await act_node(agent_state, tools=tools)
        
        assert "execution_results" in result_state
        results = result_state["execution_results"]
        assert results["success"] is True
        assert len(results["results"]) == 1
        # Results now include metadata, check the actual result value
        assert results["results"][0]["result"] == "mock_result"
    
    @pytest.mark.asyncio
    async def test_respond_node_formats_response(self, agent_state, mock_llm):
        """Respond node should format final response."""
        # Set up state with direct response
        agent_state["direct_response"] = "This is the final answer"
        agent_state["can_answer_directly"] = True
        
        result_state = await respond_node(
            agent_state,
            llm=mock_llm
        )
        
        assert "final_response" in result_state
        # Respond node generates actual LLM response, not the direct_response value
        assert result_state["final_response"] is not None


class TestWorkflowIntegration:
    """Test complete workflow integration."""
    
    @pytest.mark.asyncio
    async def test_simple_direct_response_flow(self, agent_state, mock_llm, tools):
        """Test workflow when no tools are needed."""
        # Mock reasoning to respond directly - no tool_calls means direct response
        mock_llm.invoke = AsyncMock(return_value="""
        {"reasoning": "This is a simple greeting, I can respond directly."}
        """)
        
        # Reason phase
        state = await reason_node(agent_state, llm=mock_llm, tools=tools)
        assert state["next_node"] == "respond"
        
        # Respond phase
        state = await respond_node(state, llm=mock_llm)
        assert "final_response" in state
    
    @pytest.mark.asyncio
    async def test_tool_usage_flow(self, agent_state, mock_llm, tools):
        """Test workflow when tools are needed."""
        # Mock reasoning to request calculator - using new format
        mock_llm.invoke = AsyncMock(return_value="""
        {"reasoning": "I need to use a tool for the user.", "tool_calls": [{"name": "mock_tool", "args": {"param": "test"}}]}
        """)
        
        # Reason phase
        state = await reason_node(agent_state, llm=mock_llm, tools=tools)
        assert state["next_node"] == "act"
        
        # Act phase
        state = await act_node(state, tools=tools)
        assert "execution_results" in state
        assert state["execution_results"]["success"] is True
        # Results now have metadata structure - check the actual result value
        assert state["execution_results"]["results"][0]["result"] == "mock_result"
        
        # Mock reasoning after tool execution - using new format
        mock_llm.invoke = AsyncMock(return_value="""
        {"reasoning": "Great, I got the calculation result. Now I can respond."}
        """)
        
        # Reason again (reflection)
        state = await reason_node(state, llm=mock_llm, tools=tools)
        assert state["next_node"] == "respond"
        
        # Respond phase
        state = await respond_node(state, llm=mock_llm)
        assert "final_response" in state


class TestReasoningParsing:
    """Test reasoning response parsing."""
    
    def test_parser_detects_direct_answer(self):
        """Parser should detect when LLM wants to respond directly."""
        response = """
        {"reasoning": "I can answer this directly."}
        """
        
        json_data = extract_json_from_response(response)
        assert json_data["reasoning"] == "I can answer this directly."
        # No tool_calls means direct response
    
    def test_parser_extracts_tool_calls(self):
        """Parser should extract tool calls correctly."""
        response = """
        {"reasoning": "I need to use calculator.", "tool_calls": [{"name": "calculator", "args": {"x": 5}}]}
        """
        
        json_data = extract_json_from_response(response)
        assert "tool_calls" in json_data
        tool_calls = extract_tool_calls_from_json(json_data)
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "calculator"
    
    def test_parser_handles_multiple_tools(self):
        """Parser should handle multiple tool calls."""
        response = """
        {"reasoning": "I need multiple tools.", "tool_calls": [
            {"name": "calculator", "args": {"x": 1}},
            {"name": "weather", "args": {"location": "SF"}}
        ]}
        """
        
        json_data = extract_json_from_response(response)
        tool_calls = extract_tool_calls_from_json(json_data)
        assert len(tool_calls) == 2
        assert tool_calls[0]["name"] == "calculator"
        assert tool_calls[1]["name"] == "weather"
    
    def test_parser_extracts_reasoning_text(self):
        """Parser should extract human-readable reasoning."""
        response = """
        {"reasoning": "I need to think about this carefully and consider the context."}
        """
        
        reasoning = extract_reasoning_text(response)
        assert "think about this carefully" in reasoning


class TestAdaptiveReasoning:
    """Test adaptive reasoning controls."""
    
    @pytest.mark.asyncio
    async def test_reasoning_loop_limits(self, agent_state, mock_llm, tools):
        """Should prevent infinite reasoning loops."""
        # Test the max_iterations limit in reason_node
        agent_state["current_iteration"] = 5  # At max limit
        agent_state["max_iterations"] = 5
        
        mock_llm.invoke = AsyncMock(return_value="""
        {"reasoning": "I need to use tools.", "tool_calls": [{"name": "mock_tool", "args": {"param": "test"}}]}
        """)
        
        result_state = await reason_node(agent_state, llm=mock_llm, tools=tools)
        
        # Should stop reasoning and go to respond
        assert result_state["next_node"] == "respond"
        assert result_state["stopping_reason"] == "max_iterations_reached"


class TestWorkflowErrorHandling:
    """Test workflow error handling and recovery."""
    
    @pytest.mark.asyncio
    async def test_tool_execution_error_handling(self, agent_state, tools):
        """Should handle tool execution errors gracefully."""
        # Set up invalid tool call
        agent_state["tool_calls"] = [{
            "name": "calculator",
            "args": {"operation": "invalid_op", "x1": 5, "x2": 3}
        }]
        
        result_state = await act_node(agent_state, tools=tools)
        
        # Should still have execution results, but with error
        assert "execution_results" in result_state
        results = result_state["execution_results"]
        assert results["success"] is False
        assert "errors" in results
        assert len(results["errors"]) >= 1
    
    @pytest.mark.asyncio
    async def test_malformed_reasoning_fallback(self, agent_state, mock_llm, tools):
        """Should handle malformed LLM responses gracefully."""
        # Mock LLM to return malformed JSON
        mock_llm.invoke = AsyncMock(return_value="This is not valid JSON at all")
        
        result_state = await reason_node(agent_state, llm=mock_llm, tools=tools)
        
        # Should fallback to respond node even with malformed response
        assert result_state["next_node"] == "respond"