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
        
        result_state = await respond(state, llm=mock_llm)
        
        # Should return a dict
        assert isinstance(result_state, dict)
        
        # Should have required keys
        assert "context" in result_state
        assert "response" in result_state
        assert len(result_state["context"].messages) > 0
    
    @pytest.mark.asyncio
    async def test_respond_node_direct_response(self, mock_llm):
        """Respond node should handle direct response JSON."""
        context = Context(current_input="Simple question")
        context.add_message("assistant", '{"action": "direct_response", "answer": "This is the answer"}')
        
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        result_state = await respond(state, llm=mock_llm)
        
        # Should have processed direct response
        assert result_state is not None
        messages = result_state["context"].messages
        assert len(messages) > 0
        
        # Last message should be the clean answer
        last_message = messages[-1]["content"]
        assert last_message == "This is the answer"