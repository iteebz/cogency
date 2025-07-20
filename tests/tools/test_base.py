"""Test tool base contracts and validation."""
import pytest

from cogency.tools.calculator import Calculator
from cogency.tools.base import BaseTool


class TestToolContracts:
    """Test that tools follow base contracts."""
    
    @pytest.mark.asyncio
    async def test_tool_basic_interface(self):
        """All tools must implement base interface."""
        calc = Calculator()
        
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
        calc = Calculator()
        
        # Invalid operation
        result = await calc.run(operation="invalid", x1=5, x2=3)
        assert "error" in result
        
        # Missing parameters
        result = await calc.run(operation="add", x1=5)  # Missing x2
        assert "error" in result
    
    @pytest.mark.asyncio
    async def test_execute_wrapper(self):
        """execute should catch exceptions."""
        calc = Calculator()
        
        # This should not raise an exception, even with bad input
        result = await calc.execute(operation=None, x1="not_a_number")
        assert "error" in result