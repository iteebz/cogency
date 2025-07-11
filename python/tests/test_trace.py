import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from cogency.trace import trace_node, _extract_reasoning
from cogency.types import ExecutionTrace, ExecutionStep, AgentState
from cogency.context import Context


class TestExecutionStep:
    """Test suite for ExecutionStep."""
    
    def test_execution_step_creation(self):
        """Test ExecutionStep creation."""
        step = ExecutionStep(
            node="test_node",
            input_data={"input": "test"},
            output_data={"output": "result"},
            reasoning="test reasoning"
        )
        
        assert step.node == "test_node"
        assert step.input_data == {"input": "test"}
        assert step.output_data == {"output": "result"}
        assert step.reasoning == "test reasoning"
        assert isinstance(step.timestamp, datetime)
        
    def test_execution_step_with_timestamp(self):
        """Test ExecutionStep with custom timestamp."""
        custom_time = datetime(2024, 1, 1, 12, 0, 0)
        step = ExecutionStep(
            node="test_node",
            input_data={},
            output_data={},
            reasoning="test",
            timestamp=custom_time
        )
        
        assert step.timestamp == custom_time


class TestExecutionTrace:
    """Test suite for ExecutionTrace."""
    
    def test_execution_trace_creation(self):
        """Test ExecutionTrace creation."""
        trace = ExecutionTrace(trace_id="test123")
        
        assert trace.trace_id == "test123"
        assert trace.steps == []
        
    def test_add_step(self):
        """Test adding steps to trace."""
        trace = ExecutionTrace(trace_id="test123")
        
        trace.add_step(
            node="plan",
            input_data={"query": "test"},
            output_data={"action": "respond"},
            reasoning="simple query"
        )
        
        assert len(trace.steps) == 1
        step = trace.steps[0]
        assert step.node == "plan"
        assert step.input_data == {"query": "test"}
        assert step.output_data == {"action": "respond"}
        assert step.reasoning == "simple query"
        
    def test_add_multiple_steps(self):
        """Test adding multiple steps to trace."""
        trace = ExecutionTrace(trace_id="test123")
        
        trace.add_step("plan", {}, {}, "planning")
        trace.add_step("reason", {}, {}, "reasoning")
        trace.add_step("act", {}, {}, "acting")
        
        assert len(trace.steps) == 3
        assert trace.steps[0].node == "plan"
        assert trace.steps[1].node == "reason"
        assert trace.steps[2].node == "act"
        
    def test_to_dict(self):
        """Test converting trace to dictionary."""
        trace = ExecutionTrace(trace_id="test123")
        
        trace.add_step(
            node="plan",
            input_data={"query": "test"},
            output_data={"action": "respond"},
            reasoning="simple query"
        )
        
        result = trace.to_dict()
        
        assert result["trace_id"] == "test123"
        assert len(result["steps"]) == 1
        
        step_dict = result["steps"][0]
        assert step_dict["node"] == "plan"
        assert step_dict["input_data"] == {"query": "test"}
        assert step_dict["output_data"] == {"action": "respond"}
        assert step_dict["reasoning"] == "simple query"
        assert isinstance(step_dict["timestamp"], str)  # ISO format
        
    def test_to_dict_empty_trace(self):
        """Test converting empty trace to dictionary."""
        trace = ExecutionTrace(trace_id="empty")
        
        result = trace.to_dict()
        
        assert result["trace_id"] == "empty"
        assert result["steps"] == []


class TestExtractReasoning:
    """Test suite for _extract_reasoning function."""
    
    def test_extract_reasoning_json(self):
        """Test extracting reasoning from JSON."""
        message = '{"reasoning": "I need to calculate this"}'
        
        result = _extract_reasoning(message)
        
        assert result == "Reasoning: I need to calculate this"
        
    def test_extract_strategy_json(self):
        """Test extracting strategy from JSON."""
        message = '{"strategy": "Use calculator tool"}'
        
        result = _extract_reasoning(message)
        
        assert result == "Strategy: Use calculator tool"
        
    def test_extract_assessment_json(self):
        """Test extracting assessment from JSON."""
        message = '{"assessment": "Task completed successfully"}'
        
        result = _extract_reasoning(message)
        
        assert result == "Assessment: Task completed successfully"
        
    def test_extract_description_json(self):
        """Test extracting error description from JSON."""
        message = '{"description": "Division by zero error"}'
        
        result = _extract_reasoning(message)
        
        assert result == "Error Description: Division by zero error"
        
    def test_extract_answer_json(self):
        """Test extracting direct answer from JSON."""
        message = '{"answer": "The result is 42"}'
        
        result = _extract_reasoning(message)
        
        assert result == "Direct Answer: The result is 42"
        
    def test_extract_action_json(self):
        """Test extracting action from JSON."""
        message = '{"action": "tool_needed"}'
        
        result = _extract_reasoning(message)
        
        assert result == "Action: tool_needed"
        
    def test_extract_reasoning_priority(self):
        """Test that reasoning has priority over other fields."""
        message = '{"reasoning": "Primary reason", "strategy": "Secondary strategy"}'
        
        result = _extract_reasoning(message)
        
        assert result == "Reasoning: Primary reason"
        
    def test_extract_reasoning_unexpected_json(self):
        """Test handling unexpected JSON structure."""
        message = '{"unknown_field": "some value"}'
        
        result = _extract_reasoning(message)
        
        assert result == f"LLM Output (JSON): {message}"
        
    def test_extract_reasoning_invalid_json(self):
        """Test handling invalid JSON."""
        message = '{"invalid": json}'
        
        result = _extract_reasoning(message)
        
        assert result == f"LLM Output: {message}"
        
    def test_extract_reasoning_non_json(self):
        """Test handling non-JSON text."""
        message = "Just a regular text message"
        
        result = _extract_reasoning(message)
        
        assert result == f"LLM Output: {message}"
        
    def test_extract_reasoning_empty_string(self):
        """Test handling empty string."""
        message = ""
        
        result = _extract_reasoning(message)
        
        assert result == "LLM Output: "


class TestTraceNode:
    """Test suite for trace_node decorator."""
    
    def test_trace_node_no_trace(self):
        """Test trace_node decorator when no trace is present."""
        @trace_node
        def test_func(state):
            return {"result": "success"}
            
        state = {"context": Mock(), "execution_trace": None}
        
        result = test_func(state)
        
        assert result == {"result": "success"}
        
    def test_trace_node_no_state(self):
        """Test trace_node decorator with no state."""
        @trace_node
        def test_func():
            return {"result": "success"}
            
        result = test_func()
        
        assert result == {"result": "success"}
        
    def test_trace_node_with_trace(self):
        """Test trace_node decorator with trace enabled."""
        @trace_node
        def test_func(state):
            # Simulate adding a message during execution
            state["context"].messages.append({"content": "test response"})
            return state
            
        context = Mock()
        context.messages = []
        context.tool_results = []
        context.current_input = "test input"
        
        trace = ExecutionTrace(trace_id="test123")
        state = {"context": context, "execution_trace": trace}
        
        result = test_func(state)
        
        assert len(trace.steps) == 1
        step = trace.steps[0]
        assert step.node == "test_func"
        assert step.input_data["user_query"] == "test input"
        assert step.input_data["messages"] == []
        assert step.output_data["new_messages"] == ["test response"]
        
    def test_trace_node_with_tool_results(self):
        """Test trace_node decorator with tool results."""
        @trace_node
        def act(state):
            # Simulate tool execution
            state["context"].tool_results.append({
                "tool_name": "calculator",
                "args": {"a": 2, "b": 3},
                "output": "5"
            })
            return state
            
        context = Mock()
        context.messages = []
        context.tool_results = []
        context.current_input = "calculate 2+3"
        
        trace = ExecutionTrace(trace_id="test123")
        state = {"context": context, "execution_trace": trace}
        
        result = act(state)
        
        assert len(trace.steps) == 1
        step = trace.steps[0]
        assert step.node == "act"
        assert step.output_data["tool_used"] == "calculator"
        assert step.output_data["tool_input"] == {"a": 2, "b": 3}
        assert step.output_data["tool_result"] == "5"
        assert "BaseTool Result: 5" in step.reasoning
        
    def test_trace_node_message_delta(self):
        """Test trace_node tracks message deltas correctly."""
        @trace_node
        def test_func(state):
            # Add two messages during execution
            state["context"].messages.extend([
                {"content": "message 1"},
                {"content": "message 2"}
            ])
            return state
            
        context = Mock()
        context.messages = [{"content": "existing message"}]
        context.tool_results = []
        context.current_input = "test"
        
        trace = ExecutionTrace(trace_id="test123")
        state = {"context": context, "execution_trace": trace}
        
        result = test_func(state)
        
        step = trace.steps[0]
        assert step.output_data["new_messages"] == ["message 1", "message 2"]
        
    def test_trace_node_reasoning_extraction(self):
        """Test trace_node extracts reasoning from new messages."""
        @trace_node
        def test_func(state):
            state["context"].messages.append({
                "content": '{"reasoning": "I need to think about this"}'
            })
            return state
            
        context = Mock()
        context.messages = []
        context.tool_results = []
        context.current_input = "test"
        
        trace = ExecutionTrace(trace_id="test123")
        state = {"context": context, "execution_trace": trace}
        
        result = test_func(state)
        
        step = trace.steps[0]
        assert step.reasoning == "Reasoning: I need to think about this"
        
    def test_trace_node_no_new_messages(self):
        """Test trace_node when no new messages are added."""
        @trace_node
        def test_func(state):
            return state
            
        context = Mock()
        context.messages = [{"content": "existing"}]
        context.tool_results = []
        context.current_input = "test"
        
        trace = ExecutionTrace(trace_id="test123")
        state = {"context": context, "execution_trace": trace}
        
        result = test_func(state)
        
        step = trace.steps[0]
        assert step.reasoning == "No new message added by this node."
        assert step.output_data["new_messages"] == []