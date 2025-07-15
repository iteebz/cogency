"""Tool integration tests - ZERO BULLSHIT."""
import pytest
from cogency import Agent
from cogency.tools.calculator import CalculatorTool


class TestToolIntegration:
    """Test tools work with agents."""
    
    @pytest.mark.asyncio 
    async def test_calculator_tool_integration(self, mock_llm):
        """Calculator tool works with agent."""
        calc = CalculatorTool()
        agent = Agent(name="test", llm=mock_llm, tools=[calc])
        
        # Verify tool is registered
        assert len(agent.tools) >= 1
        assert any(tool.name == "calculator" for tool in agent.tools)
        
        # Test calculation (agent will return mock response)
        result = await agent.run("Calculate 15 * 7")
        assert isinstance(result, str)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_calculator_direct_execution(self):
        """Calculator tool executes calculations correctly."""
        calc = CalculatorTool()
        
        # Test basic operations using actual run method
        result = await calc.run("add", 5, 3)
        assert result["result"] == 8
        
        result = await calc.run("multiply", 4, 7)
        assert result["result"] == 28
        
        result = await calc.run("divide", 10, 2)
        assert result["result"] == 5.0