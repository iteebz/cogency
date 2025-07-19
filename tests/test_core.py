"""Test core foundation: types, context, config, errors."""
import pytest
from datetime import datetime, UTC

from cogency.context import Context
from cogency.types import AgentState, ReasoningDecision, ToolCall
from cogency.memory.core import MemoryArtifact, MemoryType


class TestContext:
    """Test Context behavior and contracts."""
    
    def test_basic_context_creation(self):
        context = Context("test input")
        assert context.current_input == "test input"
        assert context.messages == []
        assert context.user_id == "default"
    
    def test_message_history_management(self):
        context = Context("test", max_history=2)
        
        context.add_message("user", "message 1")
        context.add_message("assistant", "response 1")
        context.add_message("user", "message 2")
        
        # Should have exactly 2 messages due to limit
        assert len(context.messages) == 2
        assert context.messages[0]["content"] == "response 1"
        assert context.messages[1]["content"] == "message 2"
    
    def test_clean_conversation_filtering(self):
        context = Context("test")
        
        # Add various message types
        context.add_message("user", "regular user message")
        context.add_message("assistant", "regular response")
        context.add_message("assistant", '{"action": "tool_needed"}')  # Should be filtered
        context.add_message("system", "system message")  # Should be filtered
        context.add_message("assistant", "TOOL_CALL: calculator")  # Should be filtered
        
        clean = context.get_clean_conversation()
        
        assert len(clean) == 2
        assert clean[0]["content"] == "regular user message"
        assert clean[1]["content"] == "regular response"
    
    def test_tool_results_tracking(self):
        context = Context("test")
        
        context.add_tool_result("calculator", {"x": 5, "y": 3}, {"result": 8})
        
        assert len(context.tool_results) == 1
        assert context.tool_results[0]["tool_name"] == "calculator"
        assert context.tool_results[0]["output"]["result"] == 8


class TestTypes:
    """Test type definitions and contracts."""
    
    def test_reasoning_decision_creation(self):
        decision = ReasoningDecision(should_respond=True, response_text="test response")
        
        assert decision.should_respond is True
        assert decision.response_text == "test response"
        assert decision.tool_calls is None
        assert decision.task_complete is False
    
    def test_tool_call_structure(self):
        tool_call = ToolCall(name="calculator", args={"operation": "add", "x": 1, "y": 2})
        
        assert tool_call.name == "calculator"
        assert tool_call.args["operation"] == "add"
    
    def test_agent_state_contract(self, context):
        state = AgentState(
            context=context,
            trace=None,
            query="test query",
            last_node_output=None
        )
        
        assert state["context"] == context
        assert state["query"] == "test query"


class TestMemoryCore:
    """Test memory types and artifacts."""
    
    def test_memory_artifact_creation(self):
        artifact = MemoryArtifact(
            content="test memory",
            memory_type=MemoryType.FACT,
            tags=["test"]
        )
        
        assert artifact.content == "test memory"
        assert artifact.memory_type == MemoryType.FACT
        assert "test" in artifact.tags
        assert artifact.id is not None
        assert isinstance(artifact.created_at, datetime)
    
    def test_decay_score_calculation(self):
        artifact = MemoryArtifact(content="test", confidence_score=1.0)
        
        # Fresh artifact should have high decay score
        score = artifact.decay_score()
        assert 0.8 < score <= 1.0  # Should be close to confidence_score
    
    def test_artifact_access_tracking(self):
        artifact = MemoryArtifact(content="test")
        
        initial_count = artifact.access_count
        initial_accessed = artifact.last_accessed
        
        # Simulate access (would be done by backend)
        artifact.access_count += 1
        artifact.last_accessed = datetime.now(UTC)
        
        assert artifact.access_count == initial_count + 1
        assert artifact.last_accessed > initial_accessed