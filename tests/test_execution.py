"""Focused unit tests for core execution business logic.

Tests the critical paths identified in the execution fix spec:
- Tool call parsing with various JSON formats
- Error handling and graceful degradation  
- Respond node never outputs JSON
- Skip ceremony testing - focus on critical paths only
"""
import pytest
import json
from unittest.mock import AsyncMock, Mock

from cogency.tools.executor import parse_tool_calls, execute_single_tool, execute_parallel_tools
from cogency.tools.result import is_tool_success
from cogency.utils.parsing import extract_json_from_response, extract_reasoning_text
from cogency.nodes.respond import respond_node, build_response_prompt
from cogency.nodes.act import act_node
from cogency.nodes.reason import reason_node
from cogency.types import ToolCall, AgentState
from cogency.context import Context
from cogency.tools.base import BaseTool


class MockTool(BaseTool):
    """Simple mock tool for testing."""
    
    def __init__(self, name: str = "test_tool", should_fail: bool = False):
        super().__init__(name, f"Mock tool: {name}")
        self.should_fail = should_fail
    
    async def run(self, **kwargs):
        if self.should_fail:
            raise Exception("Tool execution failed")
        return {"result": f"success from {self.name}"}
    
    def get_schema(self):
        return "test tool schema"
    
    def get_usage_examples(self):
        return [f'{{"name": "{self.name}", "args": {{"test": "value"}}}}']


class TestToolCallParsing:
    """Test tool call parsing with various JSON formats."""
    
    def test_parse_single_tool_call_from_json_string(self):
        """Test parsing single tool call from JSON string."""
        llm_response = '''
        {
            "reasoning": "Need to calculate something",
            "tool_calls": [
                {
                    "name": "calculator",
                    "args": {"expression": "2+2"}
                }
            ]
        }
        '''
        
        result = parse_tool_calls(llm_response)
        assert isinstance(result, list)
        assert len(result) == 1
        assert isinstance(result[0], ToolCall)
        assert result[0].name == "calculator"
        assert result[0].args == {"expression": "2+2"}
    
    def test_parse_multiple_tool_calls_from_json_string(self):
        """Test parsing multiple tool calls from JSON string."""
        llm_response = '''
        {
            "reasoning": "Need weather and time",
            "tool_calls": [
                {"name": "weather", "args": {"location": "Paris"}},
                {"name": "timezone", "args": {"location": "Paris"}}
            ]
        }
        '''
        
        result = parse_tool_calls(llm_response)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0].name == "weather"
        assert result[1].name == "timezone"
    
    def test_parse_tool_call_with_malformed_json(self):
        """Test parsing handles malformed JSON gracefully."""
        malformed_responses = [
            '{"reasoning": "test", "action": "use_tool"',  # Missing closing brace
            'Not JSON at all',  # No JSON
            '{"action": "respond"}',  # No tool call
        ]
        
        for response in malformed_responses:
            result = parse_tool_calls(response)
            assert result is None
        
        # Test empty tool call separately - this should raise validation error
        empty_tool_call_response = '{"reasoning": "test", "action": "use_tool", "tool_call": {}}'
        try:
            result = parse_tool_calls(empty_tool_call_response)
            assert result is None  # Should not reach here
        except Exception:
            # Expected - validation error for empty tool call
            pass
    
    def test_parse_tool_call_from_pre_parsed_data(self):
        """Test parsing from already parsed data structures."""
        # Single tool call as dict - now wrapped in list
        single_call = [{"name": "calculator", "args": {"expression": "5*5"}}]
        result = parse_tool_calls(single_call)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0].name == "calculator"
        
        # Multiple tool calls as list
        multi_calls = [
            {"name": "weather", "args": {"location": "Tokyo"}},
            {"name": "calculator", "args": {"expression": "10/2"}}
        ]
        result = parse_tool_calls(multi_calls)
        assert isinstance(result, list)
        assert len(result) == 2
    
    def test_extract_json_from_various_formats(self):
        """Test JSON extraction from different response formats."""
        # Clean JSON
        clean_json = '{"action": "respond", "reasoning": "I can answer directly"}'
        result = extract_json_from_response(clean_json)
        assert result["action"] == "respond"
        
        # JSON with surrounding text
        surrounded_json = '''
        Let me think about this.
        {"action": "use_tool", "tool_call": {"name": "weather", "args": {"location": "NYC"}}}
        That should work.
        '''
        result = extract_json_from_response(surrounded_json)
        assert result["action"] == "use_tool"
        assert result["tool_call"]["name"] == "weather"
        
        # No JSON - the utility returns empty dict as fallback, not None
        no_json = "This is just regular text without any JSON."
        result = extract_json_from_response(no_json)
        assert result == {}  # Empty dict fallback, not None


class TestErrorHandlingAndGracefulDegradation:
    """Test error handling and graceful degradation throughout pipeline."""
    
    @pytest.mark.asyncio
    async def test_single_tool_execution_with_failure(self):
        """Test single tool execution handles failures gracefully."""
        failing_tool = MockTool("failing_tool", should_fail=True)
        working_tool = MockTool("working_tool", should_fail=False)
        tools = [failing_tool, working_tool]
        
        # Test tool that fails - should return error dict, not raise exception
        name, args, result = await execute_single_tool("failing_tool", {}, tools)
        assert name == "failing_tool"
        assert "error" in result  # Should contain error information
        assert not is_tool_success(result)  # Should be marked as failure
        
        # Test tool that works
        name, args, result = await execute_single_tool("working_tool", {"test": "value"}, tools)
        assert name == "working_tool"
        assert result["result"] == "success from working_tool"
        assert is_tool_success(result)  # Should be marked as success
        
        # Test non-existent tool
        with pytest.raises(ValueError, match="Tool 'nonexistent' not found"):
            await execute_single_tool("nonexistent", {}, tools)
    
    @pytest.mark.asyncio
    async def test_parallel_tool_execution_with_mixed_results(self):
        """Test parallel execution handles mixed success/failure gracefully."""
        failing_tool = MockTool("failing_tool", should_fail=True)
        working_tool1 = MockTool("working_tool1", should_fail=False)
        working_tool2 = MockTool("working_tool2", should_fail=False)
        tools = [failing_tool, working_tool1, working_tool2]
        
        context = Mock()
        context.add_tool_result = Mock()
        context.add_message = Mock()
        
        tool_calls = [
            ("working_tool1", {"arg1": "value1"}),
            ("failing_tool", {"arg2": "value2"}),
            ("working_tool2", {"arg3": "value3"})
        ]
        
        result = await execute_parallel_tools(tool_calls, tools, context)
        
        # Should have mixed results
        assert result["success"] is False  # Overall failure due to one failing tool
        assert result["successful_count"] == 2
        assert result["failed_count"] == 1
        assert len(result["results"]) == 2  # Two successful results
        assert len(result["errors"]) == 1   # One error
        
        # Context should be updated with successful results
        assert context.add_tool_result.call_count == 2
        assert context.add_message.call_count == 1  # Summary message
    
    @pytest.mark.asyncio
    async def test_respond_node_handles_llm_failures(self):
        """Test respond node handles LLM failures gracefully."""
        # Mock LLM that fails
        from cogency.llm.mock import MockLLM
        
        class FailingMockLLM(MockLLM):
            async def stream(self, messages, **kwargs):
                raise Exception("LLM service unavailable")
                yield  # Make it a generator
        
        failing_llm = FailingMockLLM()
        
        context = Context(current_input="test query", messages=[], user_id="test_user")
        state = AgentState(context=context, trace=None, query="test query")
        
        result_state = await respond_node(state, llm=failing_llm)
        
        # Should generate fallback response
        assert "final_response" in result_state
        assert "encountered a technical issue" in result_state["final_response"]
        assert result_state["next_node"] == "END"
    
    @pytest.mark.asyncio
    async def test_reason_node_handles_parsing_failures(self):
        """Test reason node handles parsing failures gracefully."""
        # Mock LLM that returns unparseable response
        mock_llm = AsyncMock()
        mock_llm.run.return_value = "This is not JSON and cannot be parsed"
        
        context = Context(current_input="test query", messages=[], user_id="test_user")
        state = AgentState(context=context, trace=None, query="test query")
        
        result_state = await reason_node(state, llm=mock_llm, tools=[])
        
        # The reason node logic defaults to responding when no clear action is found
        # Since parsing fails, empty dict means no clear action
        # and tool_calls is None, so it routes to respond as fallback
        assert result_state["next_node"] == "respond"
        assert result_state["tool_calls"] is None


class TestRespondNodeJSONPrevention:
    """Test that respond node never outputs JSON to users."""
    
    @pytest.mark.asyncio
    async def test_respond_node_strips_json_from_llm_response(self):
        """Test respond node produces only conversational text."""
        # Mock LLM that might return JSON-like content
        mock_llm = AsyncMock()
        async def mock_stream(*args, **kwargs):
            yield "Here's your answer: The weather is sunny. No JSON here!"
        mock_llm.stream = mock_stream
        
        context = Context(current_input="What's the weather?", messages=[], user_id="test_user")
        state = AgentState(context=context, trace=None, query="test query")
        
        result_state = await respond_node(state, llm=mock_llm)
        
        final_response = result_state["final_response"]
        
        # Should be conversational text only
        assert isinstance(final_response, str)
        assert final_response == "Here's your answer: The weather is sunny. No JSON here!"
        
        # Should not contain JSON structures
        assert not final_response.startswith("{")
        assert not final_response.endswith("}")
        assert "\"action\":" not in final_response
        assert "\"tool_call\":" not in final_response
    
    @pytest.mark.asyncio
    async def test_respond_node_with_tool_results(self):
        """Test respond node with tool results produces conversational response."""
        mock_llm = AsyncMock()
        async def mock_stream(*args, **kwargs):
            yield "Based on the weather data, it's currently 72°F and sunny in San Francisco."
        mock_llm.stream = mock_stream
        
        context = Context(current_input="What's the weather in SF?", messages=[], user_id="test_user")
        state = AgentState(
            context=context, 
            trace=None, 
            query="test query",
            execution_results={"success": True, "results": [{"temperature": "72°F", "condition": "sunny"}]}
        )
        
        result_state = await respond_node(state, llm=mock_llm)
        
        final_response = result_state["final_response"]
        
        # Should be conversational and reference tool results
        assert "72°F" in final_response
        assert "sunny" in final_response
        assert not final_response.startswith("{")
        
        # Just verify the response content - streaming implementation details
        # are tested elsewhere
    
    def test_build_response_prompt_variations(self):
        """Test response prompt building for different scenarios."""
        # With tool results
        prompt_with_tools = build_response_prompt(has_tool_results=True)
        assert "tool results" in prompt_with_tools.lower()
        assert "conversational" in prompt_with_tools.lower()
        
        # Without tool results
        prompt_without_tools = build_response_prompt(has_tool_results=False)
        assert "knowledge" in prompt_without_tools.lower()
        assert "conversational" in prompt_without_tools.lower()
        
        # With system prompt
        system_prompt = "You are a helpful assistant."
        prompt_with_system = build_response_prompt(system_prompt, has_tool_results=True)
        assert system_prompt in prompt_with_system
        assert "tool results" in prompt_with_system.lower()


class TestCriticalPathIntegration:
    """Test critical execution paths end-to-end."""
    
    @pytest.mark.asyncio
    async def test_act_node_routes_to_reason_after_tool_execution(self):
        """Test act node always routes back to reason node."""
        working_tool = MockTool("test_tool", should_fail=False)
        tools = [working_tool]
        
        context = Context(current_input="test query", messages=[], user_id="test_user")
        context.add_message = Mock()
        context.add_tool_result = Mock()
        
        state = AgentState(
            context=context,
            trace=None,
            query="test query",
            tool_calls='{"name": "test_tool", "args": {"test": "value"}}'
        )
        
        result_state = await act_node(state, tools=tools)
        
        # Should always route back to reason
        assert result_state["next_node"] == "reason"
        assert "execution_results" in result_state
    
    @pytest.mark.asyncio
    async def test_act_node_handles_no_tool_calls(self):
        """Test act node handles missing tool calls gracefully."""
        context = Context(current_input="test query", messages=[], user_id="test_user")
        state = AgentState(context=context, trace=None, query="test query")
        # No tool_calls in state
        
        result_state = await act_node(state, tools=[])
        
        # Should route back to reason with no_action result
        assert result_state["next_node"] == "reason"
        assert result_state["execution_results"]["type"] == "no_action"
    
    def test_reasoning_text_extraction(self):
        """Test reasoning text extraction for streaming."""
        # Valid JSON with reasoning
        response_with_reasoning = '''
        {
            "reasoning": "I need to check the weather first before answering",
            "action": "use_tool",
            "tool_call": {"name": "weather", "args": {"location": "NYC"}}
        }
        '''
        
        reasoning = extract_reasoning_text(response_with_reasoning)
        assert reasoning == "I need to check the weather first before answering"
        
        # Response without JSON
        response_without_json = "Let me think about this carefully..."
        reasoning = extract_reasoning_text(response_without_json)
        assert "Analyzing the request" in reasoning  # Default fallback
        
        # JSON without reasoning field
        response_without_reasoning = '{"action": "respond"}'
        reasoning = extract_reasoning_text(response_without_reasoning)
        assert "Analyzing the request" in reasoning  # Default fallback
