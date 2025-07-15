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
        
        chunks = []
        async for chunk in plan(state, llm=mock_llm, tools=[CalculatorTool()]):
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
        assert "selected_tools" in final_state
    
    @pytest.mark.asyncio
    async def test_plan_node_tool_selection(self, mock_llm):
        """Plan node should select relevant tools."""
        context = Context(current_input="Calculate 15 * 23")
        state = {
            "context": context,
            "execution_trace": ExecutionTrace()
        }
        
        tools = [CalculatorTool()]
        final_state = None
        async for chunk in plan(state, llm=mock_llm, tools=tools):
            if chunk.get("type") == "state":
                final_state = chunk["state"]
        
        # Should have selected tools
        assert final_state is not None
        assert "selected_tools" in final_state
        assert len(final_state["selected_tools"]) > 0