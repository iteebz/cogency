"""Calculator tool unit tests."""
import pytest
from cogency.tools.calculator import CalculatorTool


class TestCalculatorTool:
    """Test calculator tool functionality."""
    
    @pytest.mark.asyncio
    async def test_add_operation(self):
        """Test addition operation."""
        calc = CalculatorTool()
        result = await calc.run("add", 5, 3)
        assert result["result"] == 8
    
    @pytest.mark.asyncio
    async def test_multiply_operation(self):
        """Test multiplication operation."""
        calc = CalculatorTool()
        result = await calc.run("multiply", 4, 7)
        assert result["result"] == 28
    
    @pytest.mark.asyncio
    async def test_divide_operation(self):
        """Test division operation."""
        calc = CalculatorTool()
        result = await calc.run("divide", 10, 2)
        assert result["result"] == 5.0
    
    @pytest.mark.asyncio
    async def test_subtract_operation(self):
        """Test subtraction operation."""
        calc = CalculatorTool()
        result = await calc.run("subtract", 10, 3)
        assert result["result"] == 7
    
    @pytest.mark.asyncio
    async def test_invalid_operation(self):
        """Test invalid operation handling."""
        calc = CalculatorTool()
        with pytest.raises(ValueError):
            await calc.run("invalid", 1, 2)
    
    @pytest.mark.asyncio
    async def test_division_by_zero(self):
        """Test division by zero handling."""
        calc = CalculatorTool()
        with pytest.raises(ValueError):
            await calc.run("divide", 10, 0)