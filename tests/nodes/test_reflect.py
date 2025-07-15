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
        
        result_state = await reflect(state, llm=mock_llm)
        
        # Should return a dict
        assert isinstance(result_state, dict)
        
        # Should have required keys
        assert "context" in result_state
        assert "reflection_response" in result_state
        assert "last_node_output" in result_state
        assert len(result_state["context"].messages) > 0
    
    @pytest.mark.asyncio
    async def test_reflect_node_adds_reflection_to_context(self, mock_llm):
        """Reflect node should add reflection to context messages."""
        context = Context(current_input="Complex analysis task")
        context.add_message("assistant", "Analysis complete with results")
        
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        result_state = await reflect(state, llm=mock_llm)
        
        # Should have added reflection message to context
        assert result_state is not None
        messages = result_state["context"].messages
        assert len(messages) > 0
        
        # Should have at least the original message plus reflection
        assert len(messages) >= 2