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
        
        chunks = []
        async for chunk in think(state, llm=mock_llm):
            chunks.append(chunk)
        
        # Should have thinking chunks and final state
        assert len(chunks) > 0
        
        # Should have thinking type chunks
        thinking_chunks = [c for c in chunks if c.get("type") == "thinking"]
        assert len(thinking_chunks) > 0
        
        # Should have final state chunk
        state_chunks = [c for c in chunks if c.get("type") == "state"]
        assert len(state_chunks) == 1
        
        # Final state should contain updated context
        final_state = state_chunks[0]["state"]
        assert "context" in final_state
        assert len(final_state["context"].messages) > 0
    
    @pytest.mark.asyncio
    async def test_think_node_adds_thinking_to_context(self, mock_llm):
        """Think node should add thinking to context messages."""
        context = Context(current_input="Complex question requiring analysis")
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        final_state = None
        async for chunk in think(state, llm=mock_llm):
            if chunk.get("type") == "state":
                final_state = chunk["state"]
        
        # Should have added thinking message to context
        assert final_state is not None
        messages = final_state["context"].messages
        assert len(messages) > 0
        
        # Should have thinking message
        thinking_msg = next((msg for msg in messages if "[THINKING]" in msg.get("content", "")), None)
        assert thinking_msg is not None