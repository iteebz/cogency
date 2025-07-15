"""Test the THINK node streaming functionality."""
import pytest
from cogency.nodes.think import think
from cogency.context import Context
from cogency.types import ExecutionTrace


class TestThinkNode:
    """Test THINK node streaming behavior."""
    
    @pytest.mark.asyncio
    async def test_think_node_streams(self, mock_llm):
        """Think node should stream thinking tokens."""
        context = Context(current_input="What is 2+2?")
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        result_state = await think(state, llm=mock_llm)
        
        # Should return a dict
        assert isinstance(result_state, dict)
        
        # Should have required keys
        assert "context" in result_state
        assert "thinking_response" in result_state
        assert "last_node_output" in result_state
        assert len(result_state["context"].messages) > 0
    
    @pytest.mark.asyncio
    async def test_think_node_adds_thinking_to_context(self, mock_llm):
        """Think node should add thinking to context messages."""
        context = Context(current_input="Complex question requiring analysis")
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        result_state = await think(state, llm=mock_llm)
        
        # Should have added thinking message to context
        assert result_state is not None
        messages = result_state["context"].messages
        assert len(messages) > 0
        
        # Should have thinking message
        thinking_msg = next((msg for msg in messages if "[THINKING]" in msg.get("content", "")), None)
        assert thinking_msg is not None