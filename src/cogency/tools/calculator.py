"""Calculator tool - safe mathematical expression evaluation with validation."""

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict

from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class CalculatorArgs:
    expression: str


@tool
class Calculator(Tool):
    # Clean template-based formatting
    human_template = "= {result}"
    agent_template = "{expression} = {result}"
    param_key = "expression"

    def __init__(self):
        super().__init__(
            name="calculator",
            description="Evaluate mathematical expressions with support for +, -, *, /, √, parentheses",
            schema="calculator(expression: str)",
            emoji="🧮",
            params=CalculatorArgs,
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
                return Result.fail("Expression contains invalid characters")

            # Safe evaluation
            safe_dict = {"__builtins__": {}}
            result = eval(expr, safe_dict, {})

            # Format result nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)

            return Result.ok({"result": result, "expression": expression})

        except ZeroDivisionError as e:
            logger.error(f"Calculator operation failed due to division by zero: {e}")
            return Result.fail("Cannot divide by zero")
        except SyntaxError as e:
            logger.error(f"Calculator operation failed due to invalid syntax: {e}")
            return Result.fail(f"Invalid expression syntax: {str(e)}")
        except TypeError as e:
            logger.error(f"Calculator operation failed due to type error: {e}")
            return Result.fail(f"Invalid expression type: {str(e)}")
        except Exception as e:
            logger.error(f"Calculator operation failed: {e}")
            return Result.fail(f"Invalid expression: {str(e)}")
