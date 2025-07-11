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
        self, operation: str, x1: float = None, x2: float = None
    ) -> Dict[str, Any]:
        if operation == "add":
            if x1 is None or x2 is None:
                return {"error": "Both x1 and x2 are required for addition."}
            result = x1 + x2
        elif operation == "subtract":
            if x1 is None or x2 is None:
                return {"error": "Both x1 and x2 are required for subtraction."}
            result = x1 - x2
        elif operation == "multiply":
            if x1 is None or x2 is None:
                return {"error": "Both x1 and x2 are required for multiplication."}
            result = x1 * x2
        elif operation == "divide":
            if x1 is None or x2 is None:
                return {"error": "Both x1 and x2 are required for division."}
            if x2 == 0:
                return {"error": "Cannot divide by zero"}
            result = x1 / x2
        elif operation == "square_root":
            if x1 is None:
                return {"error": "x1 is required for square_root."}
            if x1 < 0:
                return {"error": "Cannot calculate square root of a negative number."}
            result = math.sqrt(x1)
        else:
            return {"error": f"Unsupported operation: {operation}"}
        return {"result": result}

    def get_schema(self) -> str:
        return "calculator(operation='add|subtract|multiply|divide|square_root', x1=float, x2=float)"

    def get_usage_examples(self) -> List[str]:
        return [
            "calculator(operation='add', x1=5, x2=3)",
            "calculator(operation='multiply', x1=7, x2=8)",
            "calculator(operation='square_root', x1=9)",
        ]
