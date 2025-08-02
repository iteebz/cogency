"""Network resilience evaluation."""

import asyncio

from cogency import Agent
from cogency.tools.http import HTTP
from cogency.tools.search import Search

from ...core import Eval, FailureType


class NetworkResilience(Eval):
    """Test resilience to network failures, rate limits, and timeouts."""

    name = "network_resilience"
    description = "Test handling of API failures, rate limits, and timeouts"

    async def run(self):
        agent = Agent("resilience_tester", tools=[Search(), HTTP()], mode="fast", memory=False)

        # Test network resilience scenarios
        query = """Test network resilience by:
        1. Making an HTTP request to httpbin.org/delay/10 (should timeout)
        2. Making an HTTP request to httpbin.org/status/429 (rate limited)
        3. Making an HTTP request to nonexistent-domain-12345.com (DNS failure)
        4. Searching for 'network resilience testing' (should work)
        
        For each test, report what happened and how the system handled failures."""

        start_time = asyncio.get_event_loop().time()

        try:
            result = await asyncio.wait_for(agent.run(query), timeout=45.0)
            execution_time = asyncio.get_event_loop().time() - start_time
        except asyncio.TimeoutError:
            return self.fail(
                "Evaluation timed out - agent may not handle network issues gracefully"
            )
        except Exception as e:
            failure_result = self.fail(f"Network resilience test failed: {str(e)}")
            failure_result.failure_type = FailureType.ERROR
            return failure_result

        response_lower = result.lower()

        # Check for evidence of handling different failure modes
        handled_timeout = any(
            word in response_lower for word in ["timeout", "timed out", "slow", "delay"]
        )
        handled_rate_limit = any(
            word in response_lower for word in ["429", "rate limit", "too many requests"]
        )
        handled_dns_failure = any(
            word in response_lower for word in ["dns", "domain", "not found", "unreachable"]
        )
        successful_fallback = any(
            word in response_lower for word in ["search", "found", "resilience"]
        )

        # Check for graceful error reporting
        graceful_errors = any(
            word in response_lower for word in ["error", "failed", "unable", "issue"]
        )
        continued_operation = successful_fallback and graceful_errors

        metadata = {
            "query": query,
            "response": result,
            "execution_time": execution_time,
            "handled_timeout": handled_timeout,
            "handled_rate_limit": handled_rate_limit,
            "handled_dns_failure": handled_dns_failure,
            "successful_fallback": successful_fallback,
            "graceful_errors": graceful_errors,
            "continued_operation": continued_operation,
        }

        # Score based on resilience handling
        resilience_score = (
            sum([handled_timeout, handled_rate_limit, handled_dns_failure, continued_operation])
            / 4.0
        )

        reasonable_time = execution_time < 40.0  # Should handle failures quickly

        if resilience_score >= 0.5 and reasonable_time:
            passed = resilience_score >= 0.75
            result_obj = self.check(
                "Network resilience tested", "Network resilience tested", metadata
            )
            result_obj.score = resilience_score
            result_obj.passed = passed
            return result_obj
        else:
            issues = []
            if resilience_score < 0.5:
                issues.append(f"low resilience score ({resilience_score:.2f})")
            if not reasonable_time:
                issues.append(f"slow execution ({execution_time:.1f}s)")

            failure_result = self.fail(
                f"Insufficient network resilience: {', '.join(issues)}", metadata
            )
            failure_result.failure_type = (
                FailureType.TIMEOUT if not reasonable_time else FailureType.LOGIC
            )
            return failure_result
