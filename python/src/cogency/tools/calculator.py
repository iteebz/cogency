from typing import Any, Dict

from cogency.types import Tool

class CalculatorTool(Tool):
    name = "calculator"
    description = "A simple calculator tool that can add, subtract, multiply, and divide."

    def run(self, operation: str, num1: float, num2: float) -> Dict[str, Any]:
        if operation == "add":
            result = num1 + num2
        elif operation == "subtract":
            result = num1 - num2
        elif operation == "multiply":
            result = num1 * num2
        elif operation == "divide":
            if num2 == 0:
                return {"error": "Cannot divide by zero"}
            result = num1 / num2
        else:
            return {"error": f"Unsupported operation: {operation}"}
        return {"result": result}
