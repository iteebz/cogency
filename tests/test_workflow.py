"""Test end-to-end workflow: preprocess → reason → act → respond."""
import pytest
from unittest.mock import AsyncMock, Mock

from cogency.nodes.reason import reason_node
from cogency.nodes.act import act_node
from cogency.nodes.respond import respond_node
from cogency.reasoning.parsing import ReactResponseParser
from cogency.types import AgentState, ReasoningDecision


class TestWorkflowNodes:
    """Test individual workflow nodes."""
    
    @pytest.mark.asyncio
    async def test_reason_node_can_answer_directly(self, agent_state, mock_llm, tools):
        """Reason node should detect when it can answer directly."""
        # Mock LLM to return a direct response
        mock_llm.invoke = AsyncMock(return_value="""
        REASONING: I can answer this directly without tools.
        JSON_DECISION: {"action": "respond", "answer": "This is a direct answer"}
        """)
        
        result_state = await reason_node(
            agent_state,
            llm=mock_llm,
            tools=tools
        )
        
        assert result_state["can_answer_directly"] is True
        assert result_state["next_node"] == "respond"
        assert result_state["direct_response"] is not None
    
    @pytest.mark.asyncio
    async def test_reason_node_needs_tools(self, agent_state, mock_llm, tools):
        """Reason node should detect when tools are needed."""
        # Mock LLM to request tool usage
        mock_llm.invoke = AsyncMock(return_value="""
        REASONING: I need to calculate something first.
        JSON_DECISION: {"action": "use_tool", "tool_call": {"name": "calculator", "args": {"operation": "add", "x1": 5, "x2": 3}}}
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
            "name": "calculator",
            "args": {"operation": "add", "x1": 5, "x2": 3}
        }]
        
        result_state = await act_node(agent_state, tools=tools)
        
        assert "execution_results" in result_state
        results = result_state["execution_results"]
        assert len(results) == 1
        assert results[0]["result"] == 8
    
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
        assert result_state["final_response"] == "This is the final answer"


class TestWorkflowIntegration:
    """Test complete workflow integration."""
    
    @pytest.mark.asyncio
    async def test_simple_direct_response_flow(self, agent_state, mock_llm, tools):
        """Test workflow when no tools are needed."""
        # Mock reasoning to respond directly
        mock_llm.invoke = AsyncMock(return_value="""
        REASONING: This is a simple greeting, I can respond directly.
        JSON_DECISION: {"action": "respond", "answer": "Hello! How can I help you?"}
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
        # Mock reasoning to request calculator
        mock_llm.invoke = AsyncMock(return_value="""
        REASONING: I need to calculate 15 + 27 for the user.
        JSON_DECISION: {"action": "use_tool", "tool_call": {"name": "calculator", "args": {"operation": "add", "x1": 15, "x2": 27}}}
        """)
        
        # Reason phase
        state = await reason_node(agent_state, llm=mock_llm, tools=tools)
        assert state["next_node"] == "act"
        
        # Act phase
        state = await act_node(state, tools=tools)
        assert "execution_results" in state
        assert state["execution_results"][0]["result"] == 42
        
        # Mock reasoning after tool execution
        mock_llm.invoke = AsyncMock(return_value="""
        REASONING: Great, I got the calculation result. Now I can respond.
        JSON_DECISION: {"action": "respond", "answer": "The answer is 42"}
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
        parser = ReactResponseParser()
        
        response = """
        REASONING: I can answer this directly.
        JSON_DECISION: {"action": "respond", "answer": "Direct answer"}
        """
        
        assert parser.can_answer_directly(response) is True
        answer = parser.extract_answer(response)
        assert answer == "Direct answer"
    
    def test_parser_extracts_tool_calls(self):
        """Parser should extract tool calls correctly."""
        parser = ReactResponseParser()
        
        response = """
        REASONING: I need to use calculator.
        JSON_DECISION: {"action": "use_tool", "tool_call": {"name": "calculator", "args": {"x": 5}}}
        """
        
        assert parser.can_answer_directly(response) is False
        tool_calls = parser.extract_tool_calls(response)
        assert len(tool_calls) == 1
        assert tool_calls[0]["name"] == "calculator"
    
    def test_parser_handles_multiple_tools(self):
        """Parser should handle multiple tool calls."""
        parser = ReactResponseParser()
        
        response = """
        REASONING: I need multiple tools.
        JSON_DECISION: {"action": "use_tools", "tool_call": {"calls": [
            {"name": "calculator", "args": {"x": 1}},
            {"name": "weather", "args": {"location": "SF"}}
        ]}}
        """
        
        tool_calls = parser.extract_tool_calls(response)
        assert len(tool_calls) == 2
        assert tool_calls[0]["name"] == "calculator"
        assert tool_calls[1]["name"] == "weather"
    
    def test_parser_extracts_reasoning_text(self):
        """Parser should extract human-readable reasoning."""
        parser = ReactResponseParser()
        
        response = """
        REASONING: I need to think about this carefully and consider the context.
        JSON_DECISION: {"action": "respond", "answer": "test"}
        """
        
        reasoning = parser.extract_reasoning(response)
        assert "think about this carefully" in reasoning
        assert "JSON_DECISION" not in reasoning  # Should filter out JSON


class TestAdaptiveReasoning:
    """Test adaptive reasoning controls."""
    
    @pytest.mark.asyncio
    async def test_reasoning_loop_limits(self, agent_state, mock_llm, tools):
        """Should prevent infinite reasoning loops."""
        from cogency.reasoning.adaptive import AdaptiveController
        
        controller = AdaptiveController(max_reasoning_steps=2)
        agent_state["adaptive_controller"] = controller
        
        # Simulate multiple reasoning steps
        for i in range(3):
            should_continue, reason = controller.should_continue_reasoning()
            if not should_continue:
                break
            controller.step()
        
        # Should stop after max steps
        should_continue, reason = controller.should_continue_reasoning()
        assert should_continue is False
        assert "max_reasoning_steps" in str(reason).lower() or "limit" in str(reason).lower()


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
        assert len(results) == 1
        assert "error" in results[0]
    
    @pytest.mark.asyncio
    async def test_malformed_reasoning_fallback(self, agent_state, mock_llm, tools):
        """Should handle malformed LLM responses gracefully."""
        # Mock LLM to return malformed JSON
        mock_llm.invoke = AsyncMock(return_value="This is not valid JSON at all")
        
        result_state = await reason_node(agent_state, llm=mock_llm, tools=tools)
        
        # Should fallback to respond node even with malformed response
        assert result_state["next_node"] == "respond"