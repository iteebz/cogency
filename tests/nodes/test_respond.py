"""Test the RESPOND node streaming functionality."""
import pytest
from cogency.nodes.respond import respond
from cogency.context import Context
from cogency.types import ExecutionTrace


class TestRespondNode:
    """Test RESPOND node streaming behavior."""
    
    @pytest.mark.asyncio
    async def test_respond_node_streams(self, mock_llm):
        """Respond node should stream thinking tokens."""
        context = Context(current_input="What is 2+2?")
        context.add_message("assistant", "The calculation shows 4")
        
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        chunks = []
        async for chunk in respond(state, llm=mock_llm):
            chunks.append(chunk)
        
        # Should have thinking chunks and final state
        assert len(chunks) > 0
        
        # Should have final state chunk
        state_chunks = [c for c in chunks if c.get("type") == "state"]
        assert len(state_chunks) == 1
        
        # Final state should contain updated context
        final_state = state_chunks[0]["state"]
        assert "context" in final_state
        assert len(final_state["context"].messages) > 0
    
    @pytest.mark.asyncio
    async def test_respond_node_direct_response(self, mock_llm):
        """Respond node should handle direct response JSON."""
        context = Context(current_input="Simple question")
        context.add_message("assistant", '{"action": "direct_response", "answer": "This is the answer"}')
        
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        final_state = None
        async for chunk in respond(state, llm=mock_llm):
            if chunk.get("type") == "state":
                final_state = chunk["state"]
        
        # Should have processed direct response
        assert final_state is not None
        messages = final_state["context"].messages
        assert len(messages) > 0
        
        # Last message should be the clean answer
        last_message = messages[-1]["content"]
        assert last_message == "This is the answer"