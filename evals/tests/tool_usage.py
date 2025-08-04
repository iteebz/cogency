"""Tool usage evaluation."""

from cogency.tools.search import Search

from ..eval import Eval, EvalResult


class ToolUsage(Eval):
    """Test agent's ability to use tools effectively."""

    name = "tool_usage"
    description = "Test tool integration and usage patterns"

    async def run(self) -> EvalResult:
        test_cases = [
            "Search for information about Python list comprehensions.",
            "What are the key benefits of Python list comprehensions?",
            "Search for and summarize the performance benefits of list comprehensions.",
        ]

        def validator(response, test_case):
            response_lower = response.lower()
            return (
                any(
                    word in response_lower
                    for word in [
                        "comprehension",
                        "python",
                        "list",
                        "performance",
                        "benefit",
                        "syntax",
                    ]
                )
                and len(response) > 50
            )

        return await self.run_test_cases(test_cases, validator, "tool_user", tools=[Search()])
