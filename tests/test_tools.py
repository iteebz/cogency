"""Test tool execution, validation, and registry."""
import pytest

from cogency.tools.calculator import CalculatorTool
from cogency.tools.base import BaseTool


class TestToolContracts:
    """Test that tools follow base contracts."""
    
    @pytest.mark.asyncio
    async def test_tool_basic_interface(self):
        """All tools must implement base interface."""
        calc = CalculatorTool()
        
        # Required attributes
        assert hasattr(calc, 'name')
        assert hasattr(calc, 'description')
        assert calc.name == "calculator"
        
        # Required methods
        assert hasattr(calc, 'run')
        assert hasattr(calc, 'get_schema')
        assert hasattr(calc, 'get_usage_examples')
        
        # Schema and examples should be non-empty
        schema = calc.get_schema()
        examples = calc.get_usage_examples()
        
        assert isinstance(schema, str) and len(schema) > 0
        assert isinstance(examples, list) and len(examples) > 0
    
    @pytest.mark.asyncio
    async def test_tool_error_handling(self):
        """Tools must handle errors gracefully."""
        calc = CalculatorTool()
        
        # Invalid operation
        result = await calc.run(operation="invalid", x1=5, x2=3)
        assert "error" in result
        
        # Missing parameters
        result = await calc.run(operation="add", x1=5)  # Missing x2
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_validate_and_run_wrapper(self):
        """validate_and_run should catch exceptions."""
        calc = CalculatorTool()
        
        # This should not raise an exception, even with bad input
        result = await calc.validate_and_run(operation=None, x1="not_a_number")
        assert "error" in result


class TestCalculatorTool:
    """Test calculator tool business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        calc = CalculatorTool()
        
        # Addition
        result = await calc.run(operation="add", x1=5, x2=3)
        assert result["result"] == 8
        
        # Multiplication
        result = await calc.run(operation="multiply", x1=7, x2=8)
        assert result["result"] == 56
        
        # Division
        result = await calc.run(operation="divide", x1=10, x2=2)
        assert result["result"] == 5
    
    @pytest.mark.asyncio
    async def test_edge_cases(self):
        calc = CalculatorTool()
        
        # Division by zero
        result = await calc.run(operation="divide", x1=10, x2=0)
        assert "error" in result
        assert "divide by zero" in result["error"].lower()
        
        # Negative square root
        result = await calc.run(operation="square_root", x1=-4)
        assert "error" in result
        assert "negative" in result["error"].lower()
    
    @pytest.mark.asyncio
    async def test_square_root(self):
        calc = CalculatorTool()
        
        result = await calc.run(operation="square_root", x1=9)
        assert result["result"] == 3.0
        
        result = await calc.run(operation="square_root", x1=2)
        assert abs(result["result"] - 1.4142135623730951) < 0.0001


class TestToolRegistry:
    """Test tool auto-discovery and registration."""
    
    def test_tool_decorator_registration(self):
        """@tool decorator should register tools."""
        from cogency.tools.registry import get_registered_tools
        
        tools = get_registered_tools()
        tool_names = [t.name for t in tools]
        
        # Calculator should be auto-registered via @tool decorator
        assert "calculator" in tool_names
    
    def test_tool_discovery_contract(self):
        """All registered tools should follow contracts."""
        from cogency.tools.registry import get_registered_tools
        
        tools = get_registered_tools()
        
        for tool in tools:
            # Must inherit from BaseTool
            assert isinstance(tool, BaseTool)
            
            # Must have required attributes
            assert hasattr(tool, 'name') and tool.name
            assert hasattr(tool, 'description') and tool.description
            
            # Schema must be informative
            schema = tool.get_schema()
            assert len(schema) > 20  # Non-trivial schema
            
            # Must have examples
            examples = tool.get_usage_examples()
            assert len(examples) > 0


class TestToolExecution:
    """Test tool execution patterns and integration."""
    
    @pytest.mark.asyncio
    async def test_tool_execution_consistency(self):
        """Tool execution should be deterministic."""
        calc = CalculatorTool()
        
        # Same input should produce same output
        result1 = await calc.run(operation="multiply", x1=6, x2=7)
        result2 = await calc.run(operation="multiply", x1=6, x2=7)
        
        assert result1 == result2
        assert result1["result"] == 42
    
    @pytest.mark.asyncio
    async def test_multiple_tools_independence(self, tools):
        """Tools should not interfere with each other."""
        calc = CalculatorTool()
        
        # Execute multiple operations
        results = []
        for i in range(3):
            result = await calc.run(operation="add", x1=i, x2=1)
            results.append(result["result"])
        
        # Should get [1, 2, 3]
        assert results == [1, 2, 3]