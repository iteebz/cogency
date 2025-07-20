"""Test tool execution patterns and integration."""
import pytest

from cogency.tools.calculator import Calculator


class TestToolExecution:
    """Test tool execution patterns and integration."""
    
    @pytest.mark.asyncio
    async def test_tool_execution_consistency(self):
        """Tool execution should be deterministic."""
        calc = Calculator()
        
        # Same input should produce same output
        result1 = await calc.run(operation="multiply", x1=6, x2=7)
        result2 = await calc.run(operation="multiply", x1=6, x2=7)
        
        assert result1 == result2
        assert result1["result"] == 42
    
    @pytest.mark.asyncio
    async def test_multiple_tools_independence(self):
        """Tools should not interfere with each other."""
        calc = Calculator()
        
        # Execute multiple operations
        results = []
        for i in range(3):
            result = await calc.run(operation="add", x1=i, x2=1)
            results.append(result["result"])
        
        # Should get [1, 2, 3]
        assert results == [1, 2, 3]