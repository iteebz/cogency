"""Tool usage evaluation."""

from cogency import Agent
from cogency.tools.search import Search

from ...core import Eval, EvalResult, get_eval_notification_callback


class ToolUsage(Eval):
    """Test agent's ability to use tools effectively."""

    name = "tool_usage"
    description = "Test tool integration and usage patterns"

    # Declarative test cases
    test_cases = [
        {
            "name": "Search tool usage",
            "query": "Search for information about Python list comprehensions.",
            "expected": True,
            "parser": "_parse_search",
        },
        {
            "name": "Content quality: list comprehensions",
            "query": "What are the key benefits of Python list comprehensions?",
            "expected": True,
            "parser": "_parse_content",
        },
        {
            "name": "Tool integration: search + summarize",
            "query": "Search for and summarize the performance benefits of list comprehensions.",
            "expected": True,
            "parser": "_parse_integration",
        },
    ]

    async def run(self) -> EvalResult:
        agent = Agent(
            "tool_tester",
            tools=[Search()],
            mode="adapt",
            memory=False,
            on_notify=get_eval_notification_callback(),
            max_iterations=5,
        )

        await self.run_test_cases(agent, self.test_cases)
        return self.finalize_result()

    def _parse_search(self, result: str) -> bool:
        """Check if response indicates search tool usage."""
        response_lower = result.lower()
        return any(word in response_lower for word in ["search", "found", "according", "based on"])

    def _parse_content(self, result: str) -> bool:
        """Check if response contains relevant content."""
        response_lower = result.lower()
        return any(
            word in response_lower
            for word in ["comprehension", "concise", "readable", "efficient", "syntax"]
        )

    def _parse_integration(self, result: str) -> bool:
        """Check if response integrates search with summarization."""
        response_lower = result.lower()
        has_search = any(word in response_lower for word in ["search", "found", "according"])
        has_summary = any(
            word in response_lower for word in ["performance", "faster", "memory", "benefit"]
        )
        return has_search and has_summary
