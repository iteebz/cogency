"""Test the REFLECT node streaming functionality."""
import pytest
from cogency.nodes.reflect import reflect
from cogency.context import Context
from cogency.types import ExecutionTrace


class TestReflectNode:
    """Test REFLECT node streaming behavior."""
    
    @pytest.mark.asyncio
    async def test_reflect_node_streams(self, mock_llm):
        """Reflect node should stream thinking tokens."""
        context = Context(current_input="What is 2+2?")
        context.add_message("assistant", "The answer is 4")
        
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        chunks = []
        async for chunk in reflect(state, llm=mock_llm):
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
    async def test_reflect_node_adds_reflection_to_context(self, mock_llm):
        """Reflect node should add reflection to context messages."""
        context = Context(current_input="Complex analysis task")
        context.add_message("assistant", "Analysis complete with results")
        
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        final_state = None
        async for chunk in reflect(state, llm=mock_llm):
            if chunk.get("type") == "state":
                final_state = chunk["state"]
        
        # Should have added reflection message to context
        assert final_state is not None
        messages = final_state["context"].messages
        assert len(messages) > 0
        
        # Should have at least the original message plus reflection
        assert len(messages) >= 2