"""Agent concurrency evaluation."""

import asyncio

from cogency.tools.search import Search
from cogency.tools.shell import Shell

from ..eval import Eval


class AgentConcurrency(Eval):
    """Test multiple agents running simultaneously."""

    name = "agent_concurrency"
    description = "Test concurrent agent execution and resource management"

    async def run(self):
        # Create multiple agents with different tools
        agents = [
            self.agent("searcher", tools=[Search()], max_iterations=8),
            self.agent("commander", tools=[Shell()], max_iterations=8),
            self.agent("calculator", max_iterations=8),
        ]

        # Define concurrent tasks
        tasks = [
            "Search for 'Python asyncio tutorial' and return the first result title",
            "Run 'echo Hello from shell' command",
            "Calculate 15 * 23 + 7",
        ]

        start_time = asyncio.get_event_loop().time()
        all_traces = []

        try:
            # Execute all agents concurrently with retry logic
            async def run_with_retry(agent, task, max_retries=2):
                for attempt in range(max_retries + 1):
                    try:
                        return await asyncio.wait_for(agent.run_async(task), timeout=30.0)
                    except (asyncio.TimeoutError, Exception) as e:
                        if attempt == max_retries:
                            return e
                        await asyncio.sleep(1)  # Brief delay before retry
                return None

            results = await asyncio.gather(
                run_with_retry(agents[0], tasks[0]),
                run_with_retry(agents[1], tasks[1]),
                run_with_retry(agents[2], tasks[2]),
                return_exceptions=True,
            )

            execution_time = asyncio.get_event_loop().time() - start_time

        except asyncio.TimeoutError:
            execution_time = asyncio.get_event_loop().time() - start_time
            return {
                "name": self.name,
                "passed": False,
                "score": 0.0,
                "duration": execution_time,
                "traces": [],
                "metadata": {"execution_time": execution_time, "error": "timeout"},
            }

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

        # Success criteria
        all_completed = len(failed_results) == 0
        reasonable_time = execution_time < 75.0
        success_count = sum([search_success, shell_success, calc_success])
        score = success_count / 3.0
        passed = all_completed and reasonable_time and score >= 0.67

        for i, (task, result) in enumerate(zip(tasks, results)):
            all_traces.append(
                {
                    "task": task,
                    "result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result),
                    "success": not isinstance(result, Exception),
                    "agent_logs": agents[i].logs() if hasattr(agents[i], "logs") else [],
                }
            )

        return {
            "name": self.name,
            "passed": passed,
            "score": score,
            "duration": execution_time,
            "traces": all_traces,
            "metadata": {
                "execution_time": execution_time,
                "successful_count": len(successful_results),
                "failed_count": len(failed_results),
                "search_success": search_success,
                "shell_success": shell_success,
                "calc_success": calc_success,
            },
        }
