import re
from typing import Any, Dict, List

from cogency.tools.base import BaseTool
from cogency.tools.registry import tool


@tool
class Calculator(BaseTool):
    def __init__(self):
        super().__init__(
            name="calculator",
            description=(
                "Evaluate mathematical expressions with support for +, -, *, /, √, parentheses"
            ),
            emoji="🧮",
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
                return {"error": "Expression contains invalid characters"}

            # Safe evaluation
            safe_dict = {"__builtins__": {}}
            result = eval(expr, safe_dict, {})

            # Format result nicely
            if isinstance(result, float) and result.is_integer():
                result = int(result)

            return {"result": result}

        except ZeroDivisionError:
            return {"error": "Cannot divide by zero"}
        except Exception as e:
            return {"error": f"Invalid expression: {str(e)}"}

    def schema(self) -> str:
        return "calculator(expression='math expression')"

    def examples(self) -> List[str]:
        return [
            "calculator(expression='450 + 120*3')",
            "calculator(expression='√64')",
            "calculator(expression='(15+27)*2')",
        ]

    def format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display."""
        expr = params.get("expression", "")
        if not expr:
            return ""

        # Clean up expression for display - no spaces, add currency symbols for large numbers
        display_expr = expr.replace("**", "^").replace("*", "×").replace("/", "÷").replace(" ", "")

        # Add $ for currency-like numbers (heuristic: numbers >= 100)
        import re

        def add_currency(match):
            num = float(match.group())
            if num >= 100:
                return f"${num:,.0f}" if num == int(num) else f"${num:,.2f}"
            return match.group()

        display_expr = re.sub(r"\b\d+(?:\.\d+)?\b", add_currency, display_expr)
        return f"({display_expr})"
