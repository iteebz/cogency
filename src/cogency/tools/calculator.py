import math
from typing import Any, Dict, List

from cogency.tools.base import BaseTool
from cogency.utils.interrupt import interruptable
from cogency.utils.errors import (
    ValidationError,
    create_success_response,
    handle_tool_exception,
    validate_required_params,
)


class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description=(
                "A calculator tool that can perform basic arithmetic operations "
                "(add, subtract, multiply, divide) and calculate square roots."
            ),
        )

    @handle_tool_exception
    @interruptable
    async def run(self, operation: str, x1: float = None, x2: float = None) -> Dict[str, Any]:
        # Validate operation type
        if not operation or operation not in [
            "add",
            "subtract",
            "multiply",
            "divide",
            "square_root",
        ]:
            raise ValidationError(
                f"Unsupported operation: {operation}",
                error_code="INVALID_OPERATION",
                details={
                    "valid_operations": [
                        "add",
                        "subtract",
                        "multiply",
                        "divide",
                        "square_root",
                    ]
                },
            )

        # Validate required parameters based on operation
        if operation in ["add", "subtract", "multiply", "divide"]:
            validate_required_params({"x1": x1, "x2": x2}, ["x1", "x2"], self.name)
        elif operation == "square_root":
            validate_required_params({"x1": x1}, ["x1"], self.name)

        # Perform operation-specific validation and calculation
        if operation == "add":
            result = x1 + x2
        elif operation == "subtract":
            result = x1 - x2
        elif operation == "multiply":
            result = x1 * x2
        elif operation == "divide":
            if x2 == 0:
                raise ValidationError(
                    "Cannot divide by zero",
                    error_code="DIVISION_BY_ZERO",
                    details={"x1": x1, "x2": x2},
                )
            result = x1 / x2
        elif operation == "square_root":
            if x1 < 0:
                raise ValidationError(
                    "Cannot calculate square root of a negative number",
                    error_code="NEGATIVE_SQUARE_ROOT",
                    details={"x1": x1},
                )
            result = math.sqrt(x1)

        return create_success_response(
            {"result": result, "operation": operation}, f"Successfully performed {operation}"
        )

    def get_schema(self) -> str:
        return (
            "calculator(operation='add|subtract|multiply|divide|square_root', x1=float, x2=float)"
        )

    def get_usage_examples(self) -> List[str]:
        return [
            "calculator(operation='add', x1=5, x2=3)",
            "calculator(operation='multiply', x1=7, x2=8)",
            "calculator(operation='square_root', x1=9)",
        ]
