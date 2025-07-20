import math
from typing import Any, Dict, List

from cogency.constants import CalculatorOps, ResponseKeys
# Error handling now in BaseTool.execute() - no decorators needed
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
        # Beautiful dispatch pattern - extensible and clean
        self._operations = {
            CalculatorOps.ADD: self._add,
            CalculatorOps.SUBTRACT: self._subtract,
            CalculatorOps.MULTIPLY: self._multiply,
            CalculatorOps.DIVIDE: self._divide,
            CalculatorOps.SQUARE_ROOT: self._square_root,
        }

    async def run(self, operation: str, x1: float = None, x2: float = None, **kwargs) -> Dict[str, Any]:
        """Perform calculator operations using dispatch pattern."""
        if not operation or operation not in self._operations:
            available = ", ".join(CalculatorOps.all())
            return {ResponseKeys.ERROR: f"Invalid operation. Use: {available}"}
        
        # Dispatch to appropriate operation method
        operation_func = self._operations[operation]
        return operation_func(x1, x2)
    
    def _add(self, x1: float, x2: float) -> Dict[str, Any]:
        """Add two numbers."""
        if x1 is None or x2 is None:
            return {ResponseKeys.ERROR: "Two numbers required for addition"}
        return {ResponseKeys.RESULT: x1 + x2}
    
    def _subtract(self, x1: float, x2: float) -> Dict[str, Any]:
        """Subtract two numbers."""
        if x1 is None or x2 is None:
            return {ResponseKeys.ERROR: "Two numbers required for subtraction"}
        return {ResponseKeys.RESULT: x1 - x2}
    
    def _multiply(self, x1: float, x2: float) -> Dict[str, Any]:
        """Multiply two numbers."""
        if x1 is None or x2 is None:
            return {ResponseKeys.ERROR: "Two numbers required for multiplication"}
        return {ResponseKeys.RESULT: x1 * x2}
    
    def _divide(self, x1: float, x2: float) -> Dict[str, Any]:
        """Divide two numbers."""
        if x1 is None or x2 is None:
            return {ResponseKeys.ERROR: "Two numbers required for division"}
        if x2 == 0:
            return {ResponseKeys.ERROR: "Cannot divide by zero"}
        return {ResponseKeys.RESULT: x1 / x2}
    
    def _square_root(self, x1: float, x2: float) -> Dict[str, Any]:
        """Calculate square root of a number."""
        if x1 is None:
            return {ResponseKeys.ERROR: "Number required for square root"}
        if x1 < 0:
            return {ResponseKeys.ERROR: "Cannot calculate square root of negative number"}
        return {ResponseKeys.RESULT: math.sqrt(x1)}

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
