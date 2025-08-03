"""Network resilience evaluation."""

import asyncio

from cogency.tools.http import HTTP
from cogency.tools.scrape import Scrape
from cogency.tools.search import Search

from ..eval import Eval, EvalResult


class NetworkResilience(Eval):
    """Test resilience to network failures, rate limits, and timeouts."""

    name = "network_resilience"
    description = "Test handling of API failures, rate limits, and timeouts"

    async def run(self) -> EvalResult:
        agent = self.create_agent(
            "resilience_tester",
            tools=[Search(), HTTP(), Scrape()],
            max_iterations=12,
        )

        # Test network resilience scenarios
        query = """Test network resilience by executing ALL of these steps:
        1. Making an HTTP request to httpbin.org/delay/10 (this should timeout - use a 2 second timeout)
        2. Making an HTTP request to httpbin.org/status/429 (rate limited response)
        3. Making an HTTP request to nonexistent-domain-xyz-12345.com (DNS failure)
        4. Scraping content from httpbin.org/html (this should work)
        5. Searching for 'network resilience testing' (this should work)
        
        Execute ALL 5 tests and report what happened with each one and how you handled the failures gracefully."""

        start_time = asyncio.get_event_loop().time()

        try:
            result = await asyncio.wait_for(agent.run_async(query), timeout=30.0)
            execution_time = asyncio.get_event_loop().time() - start_time
        except asyncio.TimeoutError:
            execution_time = asyncio.get_event_loop().time() - start_time
            return EvalResult(
                name=self.name,
                passed=False,
                score=0.0,
                duration=execution_time,
                traces=[],
                metadata={"execution_time": execution_time, "error": "evaluation_timeout"},
            )
        except Exception as e:
            return EvalResult(
                name=self.name,
                passed=False,
                score=0.0,
                duration=0.0,
                traces=[],
                metadata={"error": str(e)},
            )

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
            word in response_lower for word in ["search", "found", "resilience", "scraped", "html"]
        )

        # Check for graceful error reporting
        graceful_errors = any(
            word in response_lower for word in ["error", "failed", "unable", "issue"]
        )
        continued_operation = successful_fallback and graceful_errors

        # Score based on resilience handling
        resilience_score = (
            sum([handled_timeout, handled_rate_limit, handled_dns_failure, continued_operation])
            / 4.0
        )

        reasonable_time = execution_time < 30.0
        passed = resilience_score >= 0.75 and reasonable_time

        agent_logs = agent.logs() if hasattr(agent, "logs") else []

        return EvalResult(
            name=self.name,
            passed=passed,
            score=resilience_score,
            duration=execution_time,
            traces=[{
                "query": query,
                "response": result,
                "handled_timeout": handled_timeout,
                "handled_rate_limit": handled_rate_limit,
                "handled_dns_failure": handled_dns_failure,
                "successful_fallback": successful_fallback,
                "logs": agent_logs,
            }],
            metadata={
                "execution_time": execution_time,
                "handled_timeout": handled_timeout,
                "handled_rate_limit": handled_rate_limit,
                "handled_dns_failure": handled_dns_failure,
                "successful_fallback": successful_fallback,
                "graceful_errors": graceful_errors,
                "continued_operation": continued_operation,
            },
        )