"""Tool boundary testing evaluation - migrated from archive."""

import asyncio
import time
from typing import Any

from ..judges.claude_judge import ClaudeJudge
from ..logging import EvalLogger


class ToolBoundaryTesting:
    """Test tool argument boundaries and edge case handling."""

    name = "tool_boundary_testing"
    description = "Tool argument limits, edge cases, and error handling validation"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()

    async def execute(self) -> dict[str, Any]:
        """Execute tool boundary testing evaluation."""
        from cogency import Agent

        print("🔍 Testing Tool Boundaries...")
        start_time = time.time()

        agent = Agent("boundary_tester", tools=["files", "search", "shell"], max_iterations=10)

        # Test boundary conditions and edge cases across different tools
        edge_cases = [
            "Search with empty query: ''",
            "Search for exactly 100 results about 'testing'",
            "Read a file that doesn't exist: 'nonexistent_boundary_test.txt'",
            "Write to a file with empty content in current directory: 'empty_test.txt'",
            "Execute shell command with no output: 'true'",
            "Search for a query with special characters: 'test@#$%^&*()'",
        ]

        query = f"""Test these tool boundary conditions systematically and report results:

        {chr(10).join(f"{i + 1}. {case}" for i, case in enumerate(edge_cases))}

        For each boundary test:
        - Attempt the operation exactly as described
        - Report whether it succeeded, failed, or handled gracefully
        - Note any error messages or unexpected behavior
        - Continue to the next test regardless of failures

        Complete all {len(edge_cases)} boundary tests and summarize your error handling patterns."""

        # Execute with retry logic for API failures
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                result = await agent.run_async(query)
                break
            except Exception as e:
                if "503" in str(e) and attempt < max_retries:
                    await asyncio.sleep(2**attempt)  # Exponential backoff
                    continue
                # For other errors or final attempt, create a failure response
                result = f"Tool boundary testing failed: {str(e)[:200]}"

        response_lower = result.lower()

        # Analyze boundary testing patterns
        handled_empty_inputs = any(
            phrase in response_lower for phrase in ["empty", "blank", "no query", "missing", "null"]
        )

        handled_missing_files = any(
            phrase in response_lower
            for phrase in ["not found", "doesn't exist", "missing", "file not found", "nonexistent"]
        )

        handled_limits = any(
            phrase in response_lower
            for phrase in ["limit", "maximum", "boundary", "too many", "100 results"]
        )

        handled_special_chars = any(
            phrase in response_lower for phrase in ["special", "character", "@", "#", "$", "symbol"]
        )

        graceful_error_handling = any(
            phrase in response_lower
            for phrase in ["error", "failed", "invalid", "handled", "gracefully", "caught"]
        )

        continued_testing = any(
            phrase in response_lower
            for phrase in ["next test", "continue", "moving on"]
            + ["test " + str(i) for i in range(2, 7)]
        )

        # Check systematic testing approach
        systematic_approach = any(
            phrase in response_lower
            for phrase in ["test 1", "test 2", "test 3", "boundary", "edge case", "systematically"]
        )

        # Score boundary testing quality
        boundary_indicators = [
            handled_empty_inputs,
            handled_missing_files,
            handled_limits,
            handled_special_chars,
            graceful_error_handling,
            continued_testing,
            systematic_approach,
        ]

        boundary_score = sum(boundary_indicators) / len(boundary_indicators)

        # Judge boundary testing quality
        judge_result = await self._evaluate_boundary_testing_response(
            query, result, boundary_indicators
        )

        # Log result
        self.logger.log_result(
            eval_name="tool_boundary_systematic",
            judge_result=judge_result,
            agent_metadata={
                "boundary_score": boundary_score,
                "systematic_approach": systematic_approach,
                "continued_testing": continued_testing,
            },
            execution_time=time.time() - start_time,
        )

        test_passed = (
            boundary_score >= 0.6
            and graceful_error_handling
            and continued_testing
            and judge_result.score.value >= 6.0
        )

        duration = time.time() - start_time

        return {
            "name": self.name,
            "benchmark_passed": test_passed,
            "duration": duration,
            "summary": {
                "boundary_score": boundary_score,
                "systematic_approach": systematic_approach,
                "graceful_error_handling": graceful_error_handling,
                "judge_score": judge_result.score.value,
            },
            "results": [
                {
                    "scenario": "6-boundary condition testing",
                    "query": query,
                    "response": result[:300] + "..." if len(result) > 300 else result,
                    "boundary_score": boundary_score,
                    "judge_score": judge_result.score.value,
                    "judge_reasoning": judge_result.score.reasoning,
                    "passed": test_passed,
                    "boundary_indicators": {
                        "handled_empty_inputs": handled_empty_inputs,
                        "handled_missing_files": handled_missing_files,
                        "handled_limits": handled_limits,
                        "handled_special_chars": handled_special_chars,
                        "graceful_error_handling": graceful_error_handling,
                        "continued_testing": continued_testing,
                        "systematic_approach": systematic_approach,
                    },
                }
            ],
            "metadata": {
                "evaluation_focus": "tool_boundary_testing",
                "pattern_source": "archive/tool_edges.py",
                "boundary_types": ["empty_inputs", "missing_files", "limits", "special_chars"],
                "tools_tested": ["files", "search", "shell"],
                "logging_report": self.logger.generate_report(),
            },
        }

    async def _evaluate_boundary_testing_response(
        self, query: str, response: str, indicators: list
    ):
        """Evaluate tool boundary testing quality."""

        boundary_patterns = sum(indicators)

        criteria = f"""Tool Boundary Testing Assessment:

Task: 6-boundary condition testing across multiple tools
Boundary Patterns: {boundary_patterns}/7

Rate the agent's tool boundary testing capabilities:

1. **Edge Case Recognition**: Did it identify and test boundary conditions properly?
2. **Error Handling**: Did it handle tool failures and invalid inputs gracefully?
3. **Systematic Testing**: Did it approach boundary testing methodically?
4. **Resilience**: Did it continue testing despite individual tool failures?
5. **Coverage**: Did it test diverse boundary conditions across different tools?

Score 1-3: Poor boundary testing, fails at edge cases
Score 4-6: Partial boundary testing with some error handling
Score 7-8: Good systematic boundary testing with resilience
Score 9-10: Excellent comprehensive edge case validation"""

        return await self.judge.evaluate(
            agent_response=response,
            test_case=query,
            criteria=criteria,
            context={
                "evaluation_focus": "tool_boundary_testing",
                "boundary_patterns": boundary_patterns,
                "tools_tested": ["files", "search", "shell"],
                "edge_cases": 6,
            },
        )
