"""Reading comprehension and logical reasoning evaluation."""

from cogency import Agent
from cogency.tools.search import Search

from ...core import Eval, EvalResult, get_eval_notification_callback


class Comprehension(Eval):
    """Test agent's reasoning and comprehension capabilities."""

    name = "comprehension"
    description = "Elementary logic, math, and comprehension tasks"

    # Declarative test cases
    test_cases = [
        {
            "name": "Math word problem: train speed",
            "query": "If a train travels 120 miles in 2 hours, then speeds up and travels 180 miles in the next 1.5 hours, what is its average speed for the entire journey?",
            "expected": True,
            "parser": "_check_math",
        },
        {
            "name": "Logical reasoning: syllogism validity",
            "query": "All cats are mammals. Some mammals are dogs. Therefore, some cats are dogs. Is this conclusion valid? Explain in one sentence.",
            "expected": True,
            "parser": "_check_logic",
        },
        {
            "name": "Reading comprehension: library hours",
            "query": "Text: 'The library opens at 9 AM on weekdays and 10 AM on weekends. It closes at 8 PM Monday through Thursday, 6 PM on Friday, and 5 PM on weekends.' Question: If today is Wednesday, how many hours is the library open?",
            "expected": True,
            "parser": "_check_reading",
        },
    ]

    async def run(self) -> EvalResult:
        def agent_factory():
            return Agent(
                "comprehension_tester",
                mode="reasoning",
                tools=[Search()],
                on_notify=get_eval_notification_callback(),
                max_iterations=8,
            )

        await self.run_test_cases(agent_factory, self.test_cases)
        return self.finalize_result()

    def _check_math(self, response: str) -> bool:
        """Check math word problem solution."""
        response_lower = response.lower()
        keywords = ["average", "total", "miles", "hours", "85", "86"]
        keywords_found = sum(1 for keyword in keywords if keyword in response_lower)
        return keywords_found >= len(keywords) // 2

    def _check_logic(self, response: str) -> bool:
        """Check logical reasoning validity."""
        response_lower = response.lower()
        keywords = ["invalid", "false", "incorrect", "not valid", "fallacy"]
        keywords_found = sum(1 for keyword in keywords if keyword in response_lower)
        return keywords_found >= 1

    def _check_reading(self, response: str) -> bool:
        """Check reading comprehension answer."""
        response_lower = response.lower()
        keywords = ["9", "8", "11", "hours"]
        keywords_found = sum(1 for keyword in keywords if keyword in response_lower)
        return keywords_found >= len(keywords) // 2
