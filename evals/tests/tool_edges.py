"""Tool args boundary testing evaluation."""

import asyncio

from cogency.tools.files import Files
from cogency.tools.search import Search

from ..eval import Eval


class ToolEdges(Eval):
    """Test tool args boundaries and edge cases."""

    name = "tool_edges"
    description = "Test tool args limits and error handling"

    async def run(self):
        agent = self.agent("edge_tester", tools=[Files(), Search()], max_iterations=8)

        # Test multiple edge cases - avoid security triggers
        edge_cases = [
            "Search with empty query: ''",
            "Search for exactly 100 results about 'test'",
            "Read a file that doesn't exist: 'missing_file.txt'",
            "Write to a temp file in current directory",
        ]

        query = f"""Test these tool edge cases and report what happens:
        {chr(10).join(f"{i + 1}. {case}" for i, case in enumerate(edge_cases))}
        
        For each case, try the operation and report whether it succeeded or failed gracefully."""

        # Retry logic for 503 errors
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = await agent.run_async(query)
                break
            except Exception as e:
                if "503" in str(e) and attempt < max_retries - 1:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                    continue
                raise

        response_lower = result.lower()

        # Look for evidence of proper error handling
        handled_errors = any(
            word in response_lower for word in ["error", "failed", "invalid", "not found"]
        )
        tested_limits = any(word in response_lower for word in ["limit", "maximum", "boundary"])
        graceful_handling = any(
            word in response_lower for word in ["gracefully", "handled", "caught"]
        )

        # Check if agent attempted multiple test cases
        case_indicators = [
            "empty",
            "100",
            "missing",
            "temp",
            "query",
            "results",
            "file",
            "path",
        ]
        attempted_multiple = (
            sum(1 for case in case_indicators if case in response_lower) >= 3
            or len(
                [
                    case
                    for case in edge_cases
                    if any(word in response_lower for word in case.lower().split())
                ]
            )
            >= 2
        )

        # Success requires testing boundaries and handling failures
        score = (
            1.0
            if (tested_limits and graceful_handling and handled_errors and attempted_multiple)
            else 0.8
            if (handled_errors and attempted_multiple)
            else 0.4
        )
        passed = handled_errors and attempted_multiple and score >= 0.8

        agent_logs = agent.logs() if hasattr(agent, "logs") else []

        return {
            "name": self.name,
            "passed": passed,
            "score": score,
            "duration": 0.0,
            "traces": [
                {
                    "query": query,
                    "response": result,
                    "handled_errors": handled_errors,
                    "tested_limits": tested_limits,
                    "graceful_handling": graceful_handling,
                    "attempted_multiple": attempted_multiple,
                    "logs": agent_logs,
                }
            ],
            "metadata": {
                "handled_errors": handled_errors,
                "tested_limits": tested_limits,
                "graceful_handling": graceful_handling,
                "attempted_multiple": attempted_multiple,
            },
        }
