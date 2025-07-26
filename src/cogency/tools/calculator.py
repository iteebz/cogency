import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from cogency.tools.base import BaseTool
from cogency.tools.registry import tool
from cogency.utils.results import ToolResult

logger = logging.getLogger(__name__)


@dataclass
class CalculatorParams:
    expression: str


@tool
class Calculator(BaseTool):
    # Clean template-based formatting
    human_template = "= {result}"
    agent_template = "{expression} = {result}"
    param_key = "expression"

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Evaluate mathematical expressions with support for +, -, *, /, √, parentheses",
            emoji="🧮",
            params=CalculatorParams,
            examples=[
                "calculator(expression='450 + 120*3')",
                "calculator(expression='√64')",
                "calculator(expression='(10+5)/3')",
            ],
            rules=[
                "Quick arithmetic only - for complex math use code tool",
                "Don't repeat identical calculations - check previous results first",
                "Prefer compound expressions: use (12*1.25)+(8*0.85) instead of separate steps",
            ],
        )

    async def run(self, expression: str, **kwargs) -> Dict[str, Any]:
        """Evaluate mathematical expressions - Wolfram Alpha style."""
        try:
            # Clean the expression
            expr = expression.strip()

            # Replace common symbols
            expr = expr.replace("×", "*").replace("÷", "/").replace("^", "**")

            # Handle square root
            if "√" in expr:
                expr = re.sub(r"√(\d+(?:\.\d+)?)", r"(\1)**0.5", expr)
                expr = re.sub(r"√\(([^)]+)\)", r"(\1)**0.5", expr)

            # Only allow safe characters (after symbol replacement)
            allowed_chars = set("0123456789+-*/.() ")
            if not all(c in allowed_chars for c in expr):
                return ToolResult.fail("Expression contains invalid characters")

            # Safe evaluation
            safe_dict = {"__builtins__": {}}
            result = eval(expr, safe_dict, {})

            # Format result nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)

            return ToolResult.ok({"result": result, "expression": expression})

        except ZeroDivisionError as e:
            logger.error(f"Calculator operation failed due to division by zero: {e}")
            return ToolResult.fail("Cannot divide by zero")
        except SyntaxError as e:
            logger.error(f"Calculator operation failed due to invalid syntax: {e}")
            return ToolResult.fail(f"Invalid expression syntax: {str(e)}")
        except TypeError as e:
            logger.error(f"Calculator operation failed due to type error: {e}")
            return ToolResult.fail(f"Invalid expression type: {str(e)}")
        except Exception as e:
            logger.error(f"Calculator operation failed: {e}")
            return ToolResult.fail(f"Invalid expression: {str(e)}")

