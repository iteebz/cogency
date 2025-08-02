"""Agent concurrency evaluation."""

import asyncio

from cogency import Agent
from cogency.tools.search import Search
from cogency.tools.shell import Shell

from ...core import Eval, FailureType


class AgentConcurrency(Eval):
    """Test multiple agents running simultaneously."""

    name = "agent_concurrency"
    description = "Test concurrent agent execution and resource management"

    async def run(self):
        # Create multiple agents with different tools
        agents = [
            Agent("searcher", tools=[Search()], mode="fast", memory=False),
            Agent("commander", tools=[Shell()], mode="fast", memory=False),
            Agent("calculator", tools=[], mode="fast", memory=False),
        ]

        # Define concurrent tasks
        tasks = [
            "Search for 'Python asyncio tutorial' and return the first result title",
            "Run 'echo Hello from shell' command",
            "Calculate 15 * 23 + 7",
        ]

        start_time = asyncio.get_event_loop().time()

        try:
            # Execute all agents concurrently
            results = await asyncio.gather(
                agents[0].run(tasks[0]),
                agents[1].run(tasks[1]),
                agents[2].run(tasks[2]),
                return_exceptions=True,
            )

            execution_time = asyncio.get_event_loop().time() - start_time

        except Exception as e:
            return self.fail(f"Concurrency execution failed: {str(e)}")

        # Analyze results
        successful_results = [r for r in results if not isinstance(r, Exception)]
        failed_results = [r for r in results if isinstance(r, Exception)]

        # Check for expected content in successful results
        search_success = len(successful_results) > 0 and any(
            word in str(successful_results[0]).lower()
            for word in ["python", "asyncio", "tutorial"]
            if successful_results
        )

        shell_success = len(successful_results) > 1 and any(
            "hello" in str(result).lower() for result in successful_results[1:2]
        )

        calc_success = len(successful_results) > 2 and any(
            "352" in str(result) for result in successful_results[2:3]
        )

        metadata = {
            "execution_time": execution_time,
            "successful_count": len(successful_results),
            "failed_count": len(failed_results),
            "results": [str(r)[:100] + "..." if len(str(r)) > 100 else str(r) for r in results],
            "search_success": search_success,
            "shell_success": shell_success,
            "calc_success": calc_success,
        }

        # Success criteria: All agents complete, reasonable execution time
        all_completed = len(failed_results) == 0
        reasonable_time = execution_time < 30.0  # Should complete within 30 seconds

        if all_completed and reasonable_time:
            success_count = sum([search_success, shell_success, calc_success])
            score = success_count / 3.0
            passed = score >= 0.67  # At least 2 out of 3 tasks successful

            result_obj = self.check(
                "Concurrent execution completed", "Concurrent execution completed", metadata
            )
            result_obj.score = score
            result_obj.passed = passed
            return result_obj
        else:
            issues = []
            if not all_completed:
                issues.append(f"{len(failed_results)} agent failures")
            if not reasonable_time:
                issues.append(f"slow execution ({execution_time:.1f}s)")

            failure_result = self.fail(f"Concurrency issues: {', '.join(issues)}", metadata)
            failure_result.failure_type = (
                FailureType.TIMEOUT if not reasonable_time else FailureType.ERROR
            )
            return failure_result
