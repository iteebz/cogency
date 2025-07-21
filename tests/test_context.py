"""Test Context behavior and contracts."""
import pytest

from cogency.context import Context


class TestContext:
    """Test Context behavior and contracts."""
    
    def test_basic_context_creation(self):
        context = Context("test input")
        assert context.query == "test input"
        assert context.messages == []
        assert context.user_id == "default"
    
    def test_message_history_management(self):
        context = Context("test", max_history=2)
        
        context.add_turn("user", "message 1")
        context.add_turn("assistant", "response 1")
        context.add_turn("user", "message 2")
        
        # Should have exactly 2 messages due to limit
        assert len(context.messages) == 2
        assert context.messages[0]["content"] == "response 1"
        assert context.messages[1]["content"] == "message 2"
    
    def test_clean_conversation_filtering(self):
        context = Context("test")
        
        # Add various message types
        context.add_turn("user", "regular user message")
        context.add_turn("assistant", "regular response")
        context.add_turn("assistant", '{"action": "tool_needed"}')  # Should be filtered
        context.add_turn("system", "system message")  # Should be filtered
        context.add_turn("assistant", "TOOL_CALL: calculator")  # Should be filtered
        
        clean = context.recent_turns()
        
        assert len(clean) == 2
        assert clean[0]["content"] == "regular user message"
        assert clean[1]["content"] == "regular response"
    
    def test_tool_results_tracking(self):
        context = Context("test")
        
        context.add_result("calculator", {"x": 5, "y": 3}, {"result": 8})
        
        assert len(context.tool_results) == 1
        assert context.tool_results[0]["tool_name"] == "calculator"
        assert context.tool_results[0]["output"]["result"] == 8