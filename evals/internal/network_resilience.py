"""Network resilience evaluation - migrated from archive."""

import asyncio
import time
from typing import Any

from ..judges.claude_judge import ClaudeJudge
from ..logging import EvalLogger


class NetworkResilience:
    """Test resilience to network failures, rate limits, and timeouts."""

    name = "network_resilience"
    description = "Network failure, timeout, and rate limit handling validation"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()

    async def execute(self) -> dict[str, Any]:
        """Execute network resilience evaluation."""
        from cogency import Agent

        print("🌐 Testing Network Resilience...")
        start_time = time.time()

        agent = Agent(
            "resilience_tester",
            tools=["search", "http"],  # Use available network tools
            max_iterations=12,
        )

        # Test network resilience scenarios with various failure modes
        query = """Test network resilience by executing ALL of these steps systematically:

        1. Make an HTTP request to httpbin.org/delay/10 (this should timeout - use a 2 second timeout if possible)
        2. Make an HTTP request to httpbin.org/status/429 (rate limited response expected)
        3. Make an HTTP request to nonexistent-domain-xyz-12345.com (DNS failure expected)
        4. Search for 'network resilience testing' (this should work normally)
        5. Make an HTTP request to httpbin.org/json (this should work normally)

        Execute ALL 5 tests sequentially. For each test, report:
        - What you attempted
        - What actually happened
        - How you handled any failures gracefully
        - Whether you continued to the next test

        Complete all tests and provide a summary of your resilience patterns."""

        execution_start = asyncio.get_event_loop().time()

        try:
            result = await asyncio.wait_for(agent.run_async(query), timeout=60.0)
            execution_time = asyncio.get_event_loop().time() - execution_start

        except asyncio.TimeoutError:
            execution_time = asyncio.get_event_loop().time() - execution_start

            # Log timeout result
            self.logger.log_result(
                eval_name="network_resilience_timeout",
                judge_result=None,
                agent_metadata={"execution_time": execution_time, "error": "evaluation_timeout"},
                execution_time=execution_time,
            )

            return {
                "name": self.name,
                "benchmark_passed": False,
                "duration": execution_time,
                "summary": {"error": "evaluation_timeout", "execution_time": execution_time},
                "results": [],
                "metadata": {"execution_time": execution_time, "error": "evaluation_timeout"},
            }

        except Exception as e:
            return {
                "name": self.name,
                "benchmark_passed": False,
                "duration": time.time() - start_time,
                "summary": {"error": str(e)},
                "results": [],
                "metadata": {"error": str(e)},
            }

        # Analyze network resilience patterns
        response_lower = result.lower()

        # Check for evidence of handling different failure modes
        handled_timeout = any(
            phrase in response_lower
            for phrase in ["timeout", "timed out", "delay", "slow response", "time limit"]
        )

        handled_rate_limit = any(
            phrase in response_lower
            for phrase in ["429", "rate limit", "too many requests", "rate limited", "throttled"]
        )

        handled_dns_failure = any(
            phrase in response_lower
            for phrase in [
                "dns",
                "domain not found",
                "nonexistent",
                "unreachable",
                "resolution failed",
            ]
        )

        successful_operations = any(
            phrase in response_lower
            for phrase in [
                "search",
                "found",
                "resilience",
                "httpbin.org/json",
                "successful",
                "worked",
            ]
        )

        # Check for systematic resilience patterns
        graceful_error_handling = any(
            phrase in response_lower
            for phrase in ["error", "failed", "unable", "handled", "gracefully", "continued"]
        )

        continued_after_failures = (
            successful_operations
            and graceful_error_handling
            and (handled_timeout or handled_rate_limit or handled_dns_failure)
        )

        # Count resilience indicators
        resilience_indicators = [
            handled_timeout,
            handled_rate_limit,
            handled_dns_failure,
            successful_operations,
            continued_after_failures,
        ]

        resilience_score = sum(resilience_indicators) / len(resilience_indicators)

        reasonable_time = execution_time < 45.0

        # Judge network resilience quality
        judge_result = await self._evaluate_resilience_response(
            query, result, resilience_indicators, execution_time
        )

        # Log result
        self.logger.log_result(
            eval_name="network_resilience_systematic",
            judge_result=judge_result,
            agent_metadata={
                "resilience_score": resilience_score,
                "execution_time": execution_time,
                "handled_failures": sum([handled_timeout, handled_rate_limit, handled_dns_failure]),
            },
            execution_time=time.time() - start_time,
        )

        test_passed = (
            resilience_score >= 0.6 and reasonable_time and judge_result.score.value >= 6.0
        )

        duration = time.time() - start_time

        return {
            "name": self.name,
            "benchmark_passed": test_passed,
            "duration": duration,
            "summary": {
                "resilience_score": resilience_score,
                "continued_after_failures": continued_after_failures,
                "reasonable_time": reasonable_time,
                "judge_score": judge_result.score.value,
            },
            "results": [
                {
                    "scenario": "5-step network resilience testing",
                    "query": query,
                    "response": result[:300] + "..." if len(result) > 300 else result,
                    "execution_time": execution_time,
                    "resilience_score": resilience_score,
                    "judge_score": judge_result.score.value,
                    "judge_reasoning": judge_result.score.reasoning,
                    "passed": test_passed,
                    "resilience_indicators": {
                        "handled_timeout": handled_timeout,
                        "handled_rate_limit": handled_rate_limit,
                        "handled_dns_failure": handled_dns_failure,
                        "successful_operations": successful_operations,
                        "continued_after_failures": continued_after_failures,
                        "graceful_error_handling": graceful_error_handling,
                    },
                }
            ],
            "metadata": {
                "evaluation_focus": "network_resilience",
                "pattern_source": "archive/network_resilience.py",
                "failure_modes_tested": ["timeout", "rate_limit", "dns_failure"],
                "logging_report": self.logger.generate_report(),
            },
        }

    async def _evaluate_resilience_response(
        self, query: str, response: str, indicators: list, execution_time: float
    ):
        """Evaluate network resilience quality."""

        resilience_patterns = sum(indicators)

        criteria = f"""Network Resilience Assessment:

Task: 5-step network resilience testing with intentional failures
Resilience Patterns: {resilience_patterns}/5

Rate the agent's network resilience capabilities:

1. **Failure Detection**: Did it properly identify network failures and errors?
2. **Error Handling**: Did it handle timeouts, rate limits, and DNS failures gracefully?
3. **Recovery Strategy**: Did it continue operation despite network failures?
4. **Robustness**: Did it maintain functionality with partial network connectivity?
5. **Completion**: Did it successfully complete operations that should work?

Score 1-3: Poor resilience, fails to handle network issues
Score 4-6: Partial resilience with some failure handling
Score 7-8: Good resilience with systematic error recovery
Score 9-10: Excellent robustness with comprehensive failure handling"""

        return await self.judge.evaluate(
            agent_response=response,
            test_case=query,
            criteria=criteria,
            context={
                "evaluation_focus": "network_resilience",
                "resilience_patterns": resilience_patterns,
                "execution_time": execution_time,
                "failure_modes": ["timeout", "rate_limit", "dns_failure"],
            },
        )
