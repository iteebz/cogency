from typing import Any, Dict
import math
from cogency.types import Tool

class CalculatorTool(Tool):
    name = "calculator"
    description = "A calculator tool that can perform basic arithmetic operations (add, subtract, multiply, divide) and calculate square roots."

    def run(self, operation: str, num1: float = None, num2: float = None) -> Dict[str, Any]:
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
