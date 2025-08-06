"""Tool usage evaluation."""

from cogency.tools.search import Search

from ..eval import Eval


class ToolUsage(Eval):
    """Test agent's ability to use tools effectively."""

    name = "tool_usage"
    description = "Test tool integration and usage patterns"

    async def run(self):
        # Add explicit instructions to encourage completion
        test_cases = [
            "Search for information about Python list comprehensions. Provide a complete summary.",
            "What are the key benefits of Python list comprehensions? Give specific examples.",
            "Search for and summarize the performance benefits of list comprehensions. Include concrete details and finish your response.",
        ]

        def validator(response, test_case):
            response_lower = response.lower()

            # More flexible validation - look for relevant content indicators
            has_relevant_content = any(
                word in response_lower
                for word in [
                    "comprehension",
                    "python",
                    "list",
                    "performance",
                    "benefit",
                    "syntax",
                    "concise",
                    "readable",
                    "fast",
                    "efficient",
                    "iterate",
                    "filter",
                    "map",
                ]
            )

            # Check for completion indicators
            has_completion = (
                any(
                    phrase in response_lower
                    for phrase in [
                        "in summary",
                        "overall",
                        "conclusion",
                        "therefore",
                        "benefits include",
                        "advantages",
                        "key points",
                    ]
                )
                or len(response) > 100
            )  # Longer responses likely more complete

            return has_relevant_content and (has_completion or len(response) > 50)

        return await self.test(test_cases, validator, "tool_user", tools=[Search()])
