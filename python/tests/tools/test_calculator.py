"""Tests for CalculatorTool."""

import pytest

from cogency.tools.calculator import CalculatorTool


class TestCalculatorTool:
    """Test suite for CalculatorTool."""

    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = CalculatorTool()

    @pytest.mark.asyncio
    async def test_calculator_initialization(self):
        """Test calculator initialization."""
        assert self.calculator.name == "calculator"
        assert "arithmetic" in self.calculator.description

    @pytest.mark.asyncio
    async def test_addition(self):
        """Test addition operation."""
        result = await self.calculator.run(operation="add", x1=2, x2=3)

        assert result["success"] is True
        assert result["result"] == 5
        assert result["operation"] == "add"
        assert "error" not in result

    @pytest.mark.asyncio
    async def test_subtraction(self):
        """Test subtraction operation."""
        result = await self.calculator.run(operation="subtract", x1=10, x2=3)

        assert result["success"] is True
        assert result["result"] == 7
        assert result["operation"] == "subtract"

    @pytest.mark.asyncio
    async def test_multiplication(self):
        """Test multiplication operation."""
        result = await self.calculator.run(operation="multiply", x1=4, x2=5)

        assert result["success"] is True
        assert result["result"] == 20
        assert result["operation"] == "multiply"

    @pytest.mark.asyncio
    async def test_division(self):
        """Test division operation."""
        result = await self.calculator.run(operation="divide", x1=10, x2=2)

        assert result["success"] is True
        assert result["result"] == 5.0
        assert result["operation"] == "divide"

    @pytest.mark.asyncio
    async def test_division_by_zero(self):
        """Test division by zero error."""
        result = await self.calculator.run(operation="divide", x1=10, x2=0)

        assert "error" in result
        assert "error_code" in result
        assert result["error_code"] == "DIVISION_BY_ZERO"
        assert result["tool"] == "calculator"

    @pytest.mark.asyncio
    async def test_square_root(self):
        """Test square root operation."""
        result = await self.calculator.run(operation="square_root", x1=9)

        assert result["success"] is True
        assert result["result"] == 3.0
        assert result["operation"] == "square_root"

    @pytest.mark.asyncio
    async def test_square_root_negative(self):
        """Test square root of negative number."""
        result = await self.calculator.run(operation="square_root", x1=-4)

        assert "error" in result
        assert "error_code" in result
        assert result["error_code"] == "NEGATIVE_SQUARE_ROOT"
        assert "details" in result

    @pytest.mark.asyncio
    async def test_missing_parameters_add(self):
        """Test missing parameters for addition."""
        result = await self.calculator.run(operation="add", x1=5)

        assert "error" in result
        assert result["error_code"] == "EMPTY_PARAMETERS"
        assert "x2" in result["details"]["empty_params"]

    @pytest.mark.asyncio
    async def test_missing_parameters_square_root(self):
        """Test missing parameters for square root."""
        result = await self.calculator.run(operation="square_root")

        assert "error" in result
        assert result["error_code"] == "EMPTY_PARAMETERS"
        assert "x1" in result["details"]["empty_params"]

    @pytest.mark.asyncio
    async def test_unsupported_operation(self):
        """Test unsupported operation."""
        result = await self.calculator.run(operation="power", x1=2, x2=3)

        assert "error" in result
        assert result["error_code"] == "INVALID_OPERATION"
        assert "details" in result
        assert "valid_operations" in result["details"]

    @pytest.mark.asyncio
    async def test_get_schema(self):
        """Test get_schema method."""
        schema = self.calculator.get_schema()

        assert "calculator" in schema
        assert "operation=" in schema
        assert "x1=" in schema
        assert "x2=" in schema

    @pytest.mark.asyncio
    async def test_get_usage_examples(self):
        """Test get_usage_examples method."""
        examples = self.calculator.get_usage_examples()

        assert len(examples) > 0
        assert all("calculator(" in example for example in examples)
        assert any("add" in example for example in examples)
        assert any("multiply" in example for example in examples)
        assert any("square_root" in example for example in examples)

    @pytest.mark.asyncio
    async def test_validate_and_run_success(self):
        """Test successful validation and run."""
        result = await self.calculator.validate_and_run(operation="add", x1=2, x2=3)

        assert result["success"] is True
        assert result["result"] == 5

    @pytest.mark.asyncio
    async def test_validate_and_run_error(self):
        """Test error handling in validate_and_run."""
        result = await self.calculator.validate_and_run(operation="divide", x1=10, x2=0)

        assert "error" in result
        assert result["error_code"] == "DIVISION_BY_ZERO"

    @pytest.mark.asyncio
    async def test_float_precision(self):
        """Test floating point operations."""
        result = await self.calculator.run(operation="divide", x1=1, x2=3)
        
        assert result["success"] is True
        assert abs(result["result"] - 0.3333333333333333) < 1e-10

    @pytest.mark.asyncio
    async def test_large_numbers(self):
        """Test operations with large numbers."""
        result = await self.calculator.run(operation="multiply", x1=1e6, x2=1e6)
        
        assert result["success"] is True
        assert result["result"] == 1e12

    @pytest.mark.asyncio
    async def test_zero_operations(self):
        """Test operations involving zero."""
        # Zero addition
        result = await self.calculator.run(operation="add", x1=0, x2=5)
        assert result["success"] is True
        assert result["result"] == 5
        
        # Zero multiplication
        result = await self.calculator.run(operation="multiply", x1=0, x2=100)
        assert result["success"] is True
        assert result["result"] == 0
        
        # Square root of zero
        result = await self.calculator.run(operation="square_root", x1=0)
        assert result["success"] is True
        assert result["result"] == 0