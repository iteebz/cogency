"""Mathematical reasoning evaluation."""

import re

from cogency import Agent

from ...core import Eval, EvalResult, get_eval_notification_callback


class MathReasoning(Eval):
    """Test basic mathematical reasoning capabilities."""

    name = "math_reasoning"
    description = "Test agent's ability to solve multiple math problems"

    # Declarative test cases
    test_cases = [
        {
            "name": "Basic arithmetic: 15 × 8 + 23",
            "query": "What is 15 * 8 + 23? Just give me the number.",
            "expected": 143,
            "parser": "_extract_number",
        },
        {
            "name": "Fractions: 3/4 + 1/8",
            "query": "What is 3/4 + 1/8? Give me the result as a fraction.",
            "expected": "7/8",
            "parser": "_parse_fraction",
        },
        {
            "name": "Algebra: solve 2x + 5 = 13",
            "query": "Solve for x: 2x + 5 = 13. Just give me the value of x.",
            "expected": 4,
            "parser": "_extract_number",
        },
        {
            "name": "Decimals: 0.7 × 0.3",
            "query": "What is 0.7 times 0.3? Give me the decimal result.",
            "expected": 0.21,
            "parser": "_parse_decimal",
        },
    ]

    async def run(self) -> EvalResult:
        def agent_factory():
            return Agent(
                "math_tester",
                mode="fast",
                memory=False,
                notify=True,
                on_notify=get_eval_notification_callback(),
                max_iterations=5,
            )

        await self.run_test_cases(agent_factory, self.test_cases)
        return self.finalize_result()

    def _extract_number(self, text: str) -> int:
        """Extract integer from text response."""
        numbers = re.findall(r"\b\d+\b", text)
        if numbers:
            return int(numbers[-1])
        raise ValueError(f"No number found in: {text}")

    def _parse_fraction(self, text: str) -> str:
        """Parse fraction result."""
        if any(x in text.lower() for x in ["7/8", "seven eighths", "0.875"]):
            return "7/8"
        return text.strip()

    def _parse_decimal(self, text: str) -> float:
        """Parse decimal result."""
        if "0.21" in text:
            return 0.21
        decimals = re.findall(r"\b\d*\.\d+\b", text)
        if decimals:
            return float(decimals[-1])
        raise ValueError(f"No decimal found in: {text}")
