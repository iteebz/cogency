"""Test calculator tool business logic."""
import pytest
from cogency.tools.calculator import Calculator


@pytest.fixture
def calculator():
    return Calculator()


@pytest.mark.asyncio
async def test_calculator_basic_operations(calculator):
    """Test core calculator functionality."""
    # Basic arithmetic
    result = await calculator.run(expression="2 + 2")
    assert result["result"] == 4
    
    result = await calculator.run(expression="10 - 3")
    assert result["result"] == 7
    
    result = await calculator.run(expression="7 * 8")
    assert result["result"] == 56
    
    result = await calculator.run(expression="10 / 2")
    assert result["result"] == 5
    
    # Complex expression
    result = await calculator.run(expression="(15 + 27) * 2")
    assert result["result"] == 84


@pytest.mark.asyncio
async def test_calculator_errors(calculator):
    """Test error handling."""
    # Division by zero
    result = await calculator.run(expression="4/0")
    assert "error" in result
    assert "Cannot divide by zero" in result["error"]
    
    # Code injection
    result = await calculator.run(expression="import os")
    assert "error" in result
    assert "invalid characters" in result["error"]


@pytest.mark.asyncio
async def test_calculator_schema(calculator):
    """Test schema validation."""
    schema = calculator.schema()
    examples = calculator.examples()
    
    assert "expression" in schema
    assert isinstance(examples, list)
    assert len(examples) > 0