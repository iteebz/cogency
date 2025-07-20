"""Test calculator tool business logic."""
import pytest

from cogency.tools.calculator import Calculator


class TestCalculator:
    """Test calculator business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        calc = Calculator()
        
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
        calc = Calculator()
        
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
        calc = Calculator()
        
        result = await calc.run(operation="square_root", x1=9)
        assert result["result"] == 3.0
        
        result = await calc.run(operation="square_root", x1=2)
        assert abs(result["result"] - 1.4142135623730951) < 0.0001