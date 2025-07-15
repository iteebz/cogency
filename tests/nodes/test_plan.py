"""Test the PLAN node streaming functionality."""
import pytest
from cogency.nodes.plan import plan
from cogency.context import Context
from cogency.types import ExecutionTrace
from cogency.tools.calculator import CalculatorTool


class TestPlanNode:
    """Test PLAN node streaming behavior."""
    
    @pytest.mark.asyncio
    async def test_plan_node_streams(self, mock_llm):
        """Plan node should stream thinking tokens."""
        context = Context(current_input="Calculate 2+2")
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        result_state = await plan(state, llm=mock_llm, tools=[CalculatorTool()])
        
        # Should return a dict
        assert isinstance(result_state, dict)
        
        # Should have required keys
        assert "context" in result_state
        assert "selected_tools" in result_state
        assert "plan_response" in result_state
    
    @pytest.mark.asyncio
    async def test_plan_node_tool_selection(self, mock_llm):
        """Plan node should select relevant tools."""
        context = Context(current_input="Calculate 15 * 23")
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        tools = [CalculatorTool()]
        result_state = await plan(state, llm=mock_llm, tools=tools)
        
        # Should have selected tools
        assert result_state is not None
        assert "selected_tools" in result_state
        assert len(result_state["selected_tools"]) > 0