#!/usr/bin/env python3
"""Tests for react_loop_node - the core reasoning loop architecture."""

import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from cogency.react.react_responder import react_loop_node, react_engine, reason_phase, act_phase, _complexity_score
from cogency.react.adaptive_reasoning import AdaptiveReasoningController, StoppingCriteria
from cogency.tools.base import BaseTool
from cogency.context import Context
from cogency.common.types import AgentState, ReasoningDecision


class MockLLM:
    """Mock LLM for testing."""
    
    def __init__(self, responses=None):
        self.responses = responses or []
        self.call_count = 0
        
    async def invoke(self, messages):
        """Mock invoke method."""
        if self.call_count < len(self.responses):
            response = self.responses[self.call_count]
            self.call_count += 1
            return response
        return '{"action": "respond", "answer": "Default response"}'


class MockTool(BaseTool):
    """Mock tool for testing."""
    
    def __init__(self, name: str, result: str = "mock result"):
        super().__init__(name=name, description=f"Mock tool {name}")
        self.result = result
        self.call_count = 0
    
    def get_schema(self) -> dict:
        return {"type": "object", "properties": {"query": {"type": "string"}}}
    
    def get_usage_examples(self) -> list:
        return [f"{self.name}(query='example')"]
    
    async def run(self, **kwargs):
        self.call_count += 1
        return self.result


class MockTrace:
    """Mock trace for testing."""
    
    def __init__(self):
        self.entries = []
    
    def add(self, name, message):
        self.entries.append((name, message))


class TestReactLoopNode:
    """Tests for the main react_loop_node function."""
    
    async def test_react_loop_node_initialization(self):
        """Test react_loop_node proper initialization."""
        context = Context("test query")
        trace = MockTrace()
        
        state = {
            "context": context,
            "trace": trace,
            "selected_tools": []
        }
        
        llm = MockLLM(['{"action": "respond", "answer": "Test response"}'])
        
        # Mock the react_engine to avoid complex testing
        with patch('cogency.react.react_responder.react_engine') as mock_engine:
            mock_engine.return_value = {
                "context": context,
                "text": "Test response",
                "decision": ReasoningDecision(should_respond=True, response_text="Test response", task_complete=True)
            }
            
            with patch('cogency.react.react_responder.shape_response') as mock_shape:
                mock_shape.return_value = "Shaped response"
                
                result = await react_loop_node(state, llm)
                
                assert result["context"] == context
                assert result["reasoning_decision"].should_respond is True
                assert result["last_node_output"] == "Shaped response"
                
                # Check that trace was updated
                assert len(trace.entries) == 1
                assert trace.entries[0][0] == "react_loop"
                assert "Adaptive reasoning enabled" in trace.entries[0][1]
    
    async def test_react_loop_node_complexity_based_iterations(self):
        """Test that react_loop_node sets max iterations based on complexity."""
        simple_context = Context("What is 2+2?")
        complex_context = Context("Analyze and compare the performance implications of different machine learning frameworks")
        
        trace = MockTrace()
        
        simple_state = {
            "context": simple_context,
            "trace": trace,
            "selected_tools": [MockTool("tool1"), MockTool("tool2")]
        }
        
        complex_state = {
            "context": complex_context,
            "trace": trace,
            "selected_tools": [MockTool(f"tool{i}") for i in range(10)]
        }
        
        llm = MockLLM(['{"action": "respond", "answer": "Response"}'])
        
        with patch('cogency.react.react_responder.react_engine') as mock_engine:
            mock_engine.return_value = {
                "context": simple_context,
                "text": "Response",
                "decision": ReasoningDecision(should_respond=True, response_text="Response", task_complete=True)
            }
            
            with patch('cogency.react.react_responder.shape_response') as mock_shape:
                mock_shape.return_value = "Response"
                
                # Test simple query
                await react_loop_node(simple_state, llm)
                simple_call = mock_engine.call_args_list[0]
                simple_controller = simple_call[0][3]  # Fourth argument is controller
                simple_max_iterations = simple_controller.criteria.max_iterations
                
                # Test complex query
                await react_loop_node(complex_state, llm)
                complex_call = mock_engine.call_args_list[1]
                complex_controller = complex_call[0][3]
                complex_max_iterations = complex_controller.criteria.max_iterations
                
                # Complex query should get more iterations
                assert complex_max_iterations > simple_max_iterations
                assert 3 <= simple_max_iterations <= 10
                assert 3 <= complex_max_iterations <= 10


class TestReactEngine:
    """Tests for the react_engine function."""
    
    async def test_react_engine_direct_response(self):
        """Test react_engine when agent can respond directly."""
        context = Context("What is Python?")
        state = {"context": context}
        
        llm = MockLLM(['{"action": "respond", "answer": "Python is a programming language"}'])
        tools = [MockTool("search")]
        
        controller = AdaptiveReasoningController(StoppingCriteria(max_iterations=5))
        controller.start_reasoning()
        
        # Mock reason_phase to return direct response
        with patch('cogency.react.react_responder.reason_phase') as mock_reason:
            mock_reason.return_value = {
                "can_answer_directly": True,
                "direct_response": "Python is a programming language",
                "tool_calls": None,
                "response": "Python is a programming language"
            }
            
            result = await react_engine(state, llm, tools, controller)
            
            assert result["text"] == "Python is a programming language"
            assert result["decision"].should_respond is True
            assert result["decision"].task_complete is True
            assert result["context"] == context
    
    async def test_react_engine_tool_execution_loop(self):
        """Test react_engine with tool execution loop."""
        context = Context("Search for Python information")
        state = {"context": context}
        
        llm = MockLLM([
            '{"action": "use_tool", "tool_call": {"name": "search", "args": {"query": "Python"}}}',
            '{"action": "respond", "answer": "Based on search results, Python is a programming language"}'
        ])
        tools = [MockTool("search", "Python is a programming language")]
        
        controller = AdaptiveReasoningController(StoppingCriteria(max_iterations=5))
        controller.start_reasoning()
        
        # Mock phases
        with patch('cogency.react.react_responder.reason_phase') as mock_reason, \
             patch('cogency.react.react_responder.act_phase') as mock_act:
            
            # First call: need to use tool
            # Second call: can respond directly
            mock_reason.side_effect = [
                {
                    "can_answer_directly": False,
                    "direct_response": None,
                    "tool_calls": '{"name": "search", "args": {"query": "Python"}}',
                    "response": "I need to search for Python information"
                },
                {
                    "can_answer_directly": True,
                    "direct_response": "Based on search results, Python is a programming language",
                    "tool_calls": None,
                    "response": "Based on search results, Python is a programming language"
                }
            ]
            
            mock_act.return_value = {
                "type": "tool_execution",
                "results": {"success": True, "results": ["Python is a programming language"]},
                "time": 0.1
            }
            
            result = await react_engine(state, llm, tools, controller)
            
            assert result["text"] == "Based on search results, Python is a programming language"
            assert result["decision"].should_respond is True
            assert result["decision"].task_complete is True
            assert mock_reason.call_count == 2
            assert mock_act.call_count == 1


class TestReasonPhase:
    """Tests for the reason_phase function."""
    
    async def test_reason_phase_tool_selection(self):
        """Test reason_phase selects appropriate tools."""
        context = Context("Search for Python information")
        state = {"context": context}
        
        llm = MockLLM(['{"action": "use_tool", "tool_call": {"name": "search", "args": {"query": "Python"}}}'])
        tools = [MockTool("search")]
        
        with patch('cogency.react.react_responder.ReactResponseParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.can_answer_directly.return_value = False
            mock_parser.extract_tool_calls.return_value = '{"name": "search", "args": {"query": "Python"}}'
            mock_parser.extract_answer.return_value = None
            
            result = await reason_phase(state, llm, tools)
            
            assert result["can_answer_directly"] is False
            assert result["tool_calls"] == '{"name": "search", "args": {"query": "Python"}}'
            assert result["response"] == '{"action": "use_tool", "tool_call": {"name": "search", "args": {"query": "Python"}}}'
    
    async def test_reason_phase_direct_response(self):
        """Test reason_phase when agent can respond directly."""
        context = Context("What is 2+2?")
        state = {"context": context}
        
        llm = MockLLM(['{"action": "respond", "answer": "4"}'])
        tools = []
        
        with patch('cogency.react.react_responder.ReactResponseParser') as mock_parser_class:
            mock_parser = MagicMock()
            mock_parser_class.return_value = mock_parser
            mock_parser.can_answer_directly.return_value = True
            mock_parser.extract_tool_calls.return_value = None
            mock_parser.extract_answer.return_value = "4"
            
            result = await reason_phase(state, llm, tools)
            
            assert result["can_answer_directly"] is True
            assert result["direct_response"] == "4"
            assert result["tool_calls"] is None


class TestActPhase:
    """Tests for the act_phase function."""
    
    async def test_act_phase_successful_tool_execution(self):
        """Test act_phase with successful tool execution."""
        context = Context("Search for Python")
        state = {"context": context}
        
        reasoning = {
            "tool_calls": '{"name": "search", "args": {"query": "Python"}}',
            "response": "I need to search"
        }
        
        tools = [MockTool("search", "Python is a programming language")]
        
        with patch('cogency.react.react_responder.parse_tool_call') as mock_parse, \
             patch('cogency.react.react_responder.execute_single_tool') as mock_execute:
            
            from cogency.common.schemas import ToolCall
            mock_parse.return_value = ToolCall(name="search", args={"query": "Python"})
            mock_execute.return_value = ("search", {"query": "Python"}, "Python is a programming language")
            
            result = await act_phase(reasoning, state, tools)
            
            assert result["type"] == "tool_execution"
            assert result["results"]["success"] is True
            assert "Python is a programming language" in result["results"]["results"]
    
    async def test_act_phase_no_tool_calls(self):
        """Test act_phase when no tool calls are provided."""
        context = Context("Test")
        state = {"context": context}
        
        reasoning = {
            "tool_calls": None,
            "response": "No tools needed"
        }
        
        tools = []
        
        result = await act_phase(reasoning, state, tools)
        
        assert result["type"] == "no_action"
        assert "time" in result


class TestComplexityScore:
    """Tests for the _complexity_score function (moved from test_query_complexity)."""
    
    def test_complexity_score_basic(self):
        """Test basic complexity score calculation."""
        # Simple query
        simple_score = _complexity_score("What is Python?", 2)
        assert 0.1 <= simple_score <= 0.5
        
        # Complex query
        complex_score = _complexity_score("Analyze and compare the performance implications of different machine learning frameworks", 10)
        assert 0.5 <= complex_score <= 1.0
        
        # More tools should increase complexity
        assert _complexity_score("Test query", 20) > _complexity_score("Test query", 5)
    
    def test_complexity_score_bounds(self):
        """Test complexity score is always bounded."""
        assert 0.1 <= _complexity_score("", 0) <= 1.0
        assert 0.1 <= _complexity_score("x" * 1000, 100) <= 1.0