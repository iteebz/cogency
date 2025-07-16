import math
from typing import Any, Dict, List

from cogency.tools.base import BaseTool
from cogency.tools.registry import tool


@tool
class CalculatorTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description=(
                "A calculator tool that can perform basic arithmetic operations "
                "(add, subtract, multiply, divide) and calculate square roots."
            ),
        )

    async def run(self, operation: str, x1: float = None, x2: float = None) -> Dict[str, Any]:
        """Perform calculator operations."""
        ops = ["add", "subtract", "multiply", "divide", "square_root"]
        if not operation or operation not in ops:
            return {"error": f"Invalid operation. Use: {', '.join(ops)}"}
        
        if operation in ["add", "subtract", "multiply", "divide"] and (x1 is None or x2 is None):
            return {"error": "Two numbers required for this operation"}
        
        if operation == "square_root" and x1 is None:
            return {"error": "Number required for square root"}

        if operation == "add":
            result = x1 + x2
        elif operation == "subtract":
            result = x1 - x2
        elif operation == "multiply":
            result = x1 * x2
        elif operation == "divide":
            if x2 == 0:
                return {"error": "Cannot divide by zero"}
            result = x1 / x2
        elif operation == "square_root":
            if x1 < 0:
                return {"error": "Cannot calculate square root of negative number"}
            result = math.sqrt(x1)
        
        return {"result": result}

    def get_schema(self) -> str:
        return (
            "calculator(operation='add|subtract|multiply|divide|square_root', x1=float, x2=float) - "
            "Examples: calculator(operation='multiply', x1=180, x2=3) for 180*3, "
            "calculator(operation='add', x1=1200, x2=540) for 1200+540"
        )

    def get_usage_examples(self) -> List[str]:
        return [
            "calculator(operation='add', x1=5, x2=3)",
            "calculator(operation='multiply', x1=7, x2=8)",
            "calculator(operation='square_root', x1=9)",
        ]
