import logging
import re
from typing import Any, Dict, Optional

from cogency.tools.base import BaseTool
from cogency.tools.registry import tool
from cogency.utils.results import ToolResult

logger = logging.getLogger(__name__)


@tool
class Calculator(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description="Evaluate mathematical expressions with support for +, -, *, /, √, parentheses",
            emoji="🧮",
            schema="calculator(expression='2+3*4 or √64 or (10+5)/3')\nRequired: expression",
            examples=[
                "calculator(expression='450 + 120*3')",
                "calculator(expression='√64')",
                "calculator(expression='(10+5)/3')",
            ],
            rules=[
                "Quick arithmetic only - for complex math use code tool",
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

            return ToolResult.ok({"result": result})

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

    def format_human(
        self, params: Dict[str, Any], results: Optional[ToolResult] = None
    ) -> tuple[str, str]:
        """Format calculator execution for display."""
        expr = params.get("expression", "")
        if not expr:
            param_str = ""
        else:
            # Clean up expression for display
            display_expr = (
                expr.replace("**", "^").replace("*", "×").replace("/", "÷").replace(" ", "")
            )
            param_str = f"({display_expr})"

        if results is None:
            return param_str, ""

        # Format results
        if results.failure:
            result_str = f"Error: {results.error}"
        else:
            result = results.data.get("result", "")
            result_str = f"= {result}"

        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format calculator results for agent action history."""
        if not result_data:
            return "No result"
        result = result_data.get("result", "")
        return f"= {result}"
