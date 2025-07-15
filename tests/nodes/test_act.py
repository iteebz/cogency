"""Test the ACT node streaming functionality."""
import pytest
from cogency.nodes.act import act
from cogency.context import Context
from cogency.types import ExecutionTrace
from cogency.tools.calculator import CalculatorTool


class TestActNode:
    """Test ACT node streaming behavior."""
    
    @pytest.mark.asyncio
    async def test_act_node_returns_dict(self, mock_llm):
        """Act node should return dict state for LangGraph compatibility."""
        context = Context(current_input="Calculate 2+2")
        # Add a tool call to the context
        context.add_message("assistant", 'TOOL_CALL: calculator(expression="2+2")')
        
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        result = await act(state, tools=[CalculatorTool()])
        
        # Should return a dict
        assert isinstance(result, dict)
        
        # Should have required keys
        assert "context" in result
        assert "execution_trace" in result
        
        # Context should be updated
        assert result["context"] is not None
    
    @pytest.mark.asyncio
    async def test_act_node_no_tool_call(self, mock_llm):
        """Act node should handle cases with no tool call."""
        context = Context(current_input="Just a regular message")
        context.add_message("assistant", "This is just a regular response")
        
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        result = await act(state, tools=[CalculatorTool()])
        
        # Should return a dict
        assert isinstance(result, dict)
        
        # Should have required keys
        assert "context" in result
        assert "execution_trace" in result
        
        # Context should be returned unchanged or minimally modified
        assert result["context"] is not None