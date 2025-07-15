"""BaseTool primitive test - ZERO BULLSHIT."""
import pytest
from cogency.tools.base import BaseTool


class SimpleCalculator(BaseTool):
    def __init__(self):
        super().__init__(name="simple_calc", description="Simple calc")
    
    async def run(self, x: int, y: int) -> dict:
        return {"result": x + y}
    
    def get_schema(self) -> str:
        return "simple_calc(x=int, y=int)"
    
    def get_usage_examples(self) -> list:
        return ["simple_calc(x=1, y=2)"]


class TestBaseTool:
    @pytest.mark.asyncio
    async def test_tool_interface(self):
        """BaseTool has required interface."""
        tool = SimpleCalculator()
        assert tool.name == "simple_calc"
        assert tool.description == "Simple calc"
        
        result = await tool.run(x=5, y=3)
        assert result["result"] == 8