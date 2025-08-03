"""Tool args boundary testing evaluation."""

from cogency import Agent
from cogency.tools.files import Files
from cogency.tools.search import Search

from ...core import Eval, FailureType


class ToolEdges(Eval):
    """Test tool args boundaries and edge cases."""

    name = "tool_edges"
    description = "Test tool args limits and error handling"

    async def run(self):
        agent = Agent(
            "edge_tester", tools=[Files(), Search()], mode="fast", memory=False, max_iterations=8
        )

        # Test multiple edge cases
        edge_cases = [
            "Search with empty query: ''",
            "Search for exactly 100 results about 'test'",
            "Read a file that doesn't exist: '/nonexistent/path/file.txt'",
            "Write to invalid path: '/root/protected/file.txt'",
        ]

        query = f"""Test these edge cases and report what happens:
        {chr(10).join(f"{i + 1}. {case}" for i, case in enumerate(edge_cases))}
        
        For each case, try the operation and report whether it succeeded or failed gracefully."""

        result = await agent.run_async(query)
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
            "nonexistent",
            "protected",
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

        metadata = {
            "query": query,
            "response": result,
            "handled_errors": handled_errors,
            "tested_limits": tested_limits,
            "graceful_handling": graceful_handling,
            "attempted_multiple": attempted_multiple,
        }

        # Success requires testing boundaries and handling failures
        if handled_errors and attempted_multiple:
            score = 1.0 if (tested_limits and graceful_handling) else 0.8
            passed = score >= 0.8
            result_obj = self.check(
                "Boundary testing completed", "Boundary testing completed", metadata
            )
            result_obj.score = score
            result_obj.passed = passed
            return result_obj
        else:
            missing = []
            if not handled_errors:
                missing.append("error handling")
            if not attempted_multiple:
                missing.append("multiple test cases")

            failure_result = self.fail(
                f"Insufficient boundary testing - missing: {', '.join(missing)}", metadata
            )
            failure_result.failure_type = FailureType.LOGIC
            return failure_result
