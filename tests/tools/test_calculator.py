"""Test calculator tool business logic."""
import pytest

from cogency.tools.calculator import Calculator


class TestCalculator:
    """Test calculator business logic."""
    
    @pytest.mark.asyncio
    async def test_basic_arithmetic(self):
        """Test basic arithmetic operations."""
        calc = Calculator()
        
        # Addition
        result = await calc.run(expression="2 + 2")
        assert result["result"] == 4
        
        # Subtraction
        result = await calc.run(expression="10 - 3")
        assert result["result"] == 7
        
        # Multiplication
        result = await calc.run(expression="7 * 8")
        assert result["result"] == 56
        
        # Division
        result = await calc.run(expression="10 / 2")
        assert result["result"] == 5
    
    @pytest.mark.asyncio
    async def test_powers(self):
        """Test power operations with ^ and ** syntax."""
        calc = Calculator()
        
        # Caret syntax
        result = await calc.run(expression="9^3")
        assert result["result"] == 729
        
        # Python syntax
        result = await calc.run(expression="2**8")
        assert result["result"] == 256
        
        # Fractional powers
        result = await calc.run(expression="8^(1/3)")
        assert abs(result["result"] - 2.0) < 0.0001
    
    @pytest.mark.asyncio
    async def test_square_roots(self):
        """Test square root operations."""
        calc = Calculator()
        
        # Simple square root
        result = await calc.run(expression="√25")
        assert result["result"] == 5
        
        # Square root of perfect square
        result = await calc.run(expression="√64")
        assert result["result"] == 8
        
        # Complex square root expression
        result = await calc.run(expression="√(36+49)")
        assert abs(result["result"] - 9.219544457292887) < 0.0001
        
        # Square root with decimals
        result = await calc.run(expression="√2")
        assert abs(result["result"] - 1.4142135623730951) < 0.0001
    
    @pytest.mark.asyncio
    async def test_complex_expressions(self):
        """Test complex mathematical expressions."""
        calc = Calculator()
        
        # Parentheses
        result = await calc.run(expression="(15 + 27) * 2")
        assert result["result"] == 84
        
        # Mixed operations
        result = await calc.run(expression="450 + 120 * 3")
        assert result["result"] == 810
        
        # Nested parentheses
        result = await calc.run(expression="((5 + 3) * 2) - 1")
        assert result["result"] == 15
    
    @pytest.mark.asyncio
    async def test_symbol_replacement(self):
        """Test that common math symbols are properly replaced."""
        calc = Calculator()
        
        # Multiplication symbol
        result = await calc.run(expression="5 × 6")
        assert result["result"] == 30
        
        # Division symbol
        result = await calc.run(expression="20 ÷ 4")
        assert result["result"] == 5
        
        # Mixed symbols
        result = await calc.run(expression="10 × 3 ÷ 2")
        assert result["result"] == 15
    
    @pytest.mark.asyncio
    async def test_error_cases(self):
        """Test error handling for various invalid inputs."""
        calc = Calculator()
        
        # Division by zero
        result = await calc.run(expression="4/0")
        assert "error" in result
        assert "Cannot divide by zero" in result["error"]
        
        # Invalid characters - code injection attempt
        result = await calc.run(expression="import os")
        assert "error" in result
        assert "Expression contains invalid characters" in result["error"]
        
        # Invalid characters - function calls
        result = await calc.run(expression="print('hello')")
        assert "error" in result
        assert "Expression contains invalid characters" in result["error"]
        
        # Invalid characters - variable assignment
        result = await calc.run(expression="x = 5")
        assert "error" in result
        assert "Expression contains invalid characters" in result["error"]
        
        # Malformed expression
        result = await calc.run(expression="5 + * 3")
        assert "error" in result
        assert "Invalid expression" in result["error"]
    
    @pytest.mark.asyncio
    async def test_edge_values(self):
        """Test edge cases with special values."""
        calc = Calculator()
        
        # Zero operations
        result = await calc.run(expression="0 + 0")
        assert result["result"] == 0
        
        result = await calc.run(expression="0 * 100")
        assert result["result"] == 0
        
        # Negative numbers
        result = await calc.run(expression="-5 + 3")
        assert result["result"] == -2
        
        result = await calc.run(expression="(-2) * 3")
        assert result["result"] == -6
        
        # Decimal operations
        result = await calc.run(expression="3.14 * 2")
        assert abs(result["result"] - 6.28) < 0.0001
    
    @pytest.mark.asyncio
    async def test_whitespace_handling(self):
        """Test that whitespace is handled properly."""
        calc = Calculator()
        
        # Extra spaces
        result = await calc.run(expression="  5   +   3  ")
        assert result["result"] == 8
        
        # No spaces
        result = await calc.run(expression="5+3")
        assert result["result"] == 8
        
        # Mixed spacing
        result = await calc.run(expression="5+ 3*2")
        assert result["result"] == 11