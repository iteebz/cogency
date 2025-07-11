import math
from typing import Any, Dict, List

from cogency.tools.base import BaseTool


class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="A calculator tool that can perform basic arithmetic operations (add, subtract, multiply, divide) and calculate square roots.",
        )

    def run(
        self, operation: str, num1: float = None, num2: float = None
    ) -> Dict[str, Any]:
        if operation == "add":
            if num1 is None or num2 is None:
                return {"error": "Both num1 and num2 are required for addition."}
            result = num1 + num2
        elif operation == "subtract":
            if num1 is None or num2 is None:
                return {"error": "Both num1 and num2 are required for subtraction."}
            result = num1 - num2
        elif operation == "multiply":
            if num1 is None or num2 is None:
                return {"error": "Both num1 and num2 are required for multiplication."}
            result = num1 * num2
        elif operation == "divide":
            if num1 is None or num2 is None:
                return {"error": "Both num1 and num2 are required for division."}
            if num2 == 0:
                return {"error": "Cannot divide by zero"}
            result = num1 / num2
        elif operation == "square_root":
            if num1 is None:
                return {"error": "num1 is required for square_root."}
            if num1 < 0:
                return {"error": "Cannot calculate square root of a negative number."}
            result = math.sqrt(num1)
        else:
            return {"error": f"Unsupported operation: {operation}"}
        return {"result": result}

    def get_schema(self) -> str:
        return "calculator(operation='add|subtract|multiply|divide|square_root', num1=float, num2=float)"

    def get_usage_examples(self) -> List[str]:
        return [
            "calculator(operation='add', num1=5, num2=3)",
            "calculator(operation='multiply', num1=7, num2=8)",
            "calculator(operation='square_root', num1=9)",
        ]
