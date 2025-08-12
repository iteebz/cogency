"""Agent concurrency evaluation - migrated from archive."""

import asyncio
import time
from typing import Any

from ..judges.claude_judge import ClaudeJudge
from ..logging import EvalLogger


class AgentConcurrency:
    """Test multiple agents running simultaneously with resource management."""

    name = "agent_concurrency"
    description = "Multi-agent concurrent execution and resource isolation"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()

    async def execute(self) -> dict[str, Any]:
        """Execute concurrent agent evaluation."""
        from cogency import Agent

        print("⚡ Testing Agent Concurrency...")
        start_time = time.time()

        # Create agents with different tool configurations
        agents = [
            Agent("concurrent_searcher", tools=["search"], max_iterations=8),
            Agent("concurrent_shell", tools=["shell"], max_iterations=8),
            Agent("concurrent_calculator", max_iterations=8),
        ]

        # Define concurrent tasks for parallel execution
        tasks = [
            "Search for 'Python asyncio tutorial' and return the first result title",
            "Run 'echo Hello from concurrent shell' command",
            "Calculate 15 * 23 + 7 and show your work",
        ]

        execution_start = asyncio.get_event_loop().time()

        try:
            # Execute agents concurrently with retry logic and timeout
            async def run_with_retry(agent, task, max_retries=2):
                for attempt in range(max_retries + 1):
                    try:
                        return await asyncio.wait_for(agent.run_async(task), timeout=30.0)
                    except (asyncio.TimeoutError, Exception) as e:
                        if attempt == max_retries:
                            return f"Failed after {max_retries + 1} attempts: {str(e)[:100]}"
                        await asyncio.sleep(1)  # Brief delay before retry
                return "Retry exhausted"

            # Run all agents concurrently
            results = await asyncio.wait_for(
                asyncio.gather(
                    run_with_retry(agents[0], tasks[0]),
                    run_with_retry(agents[1], tasks[1]),
                    run_with_retry(agents[2], tasks[2]),
                    return_exceptions=True,
                ),
                timeout=60.0,
            )

            execution_time = asyncio.get_event_loop().time() - execution_start

        except asyncio.TimeoutError:
            execution_time = asyncio.get_event_loop().time() - execution_start

            # Log timeout result
            self.logger.log_result(
                eval_name="concurrent_agents_timeout",
                judge_result=None,
                agent_metadata={"execution_time": execution_time, "error": "timeout"},
                execution_time=execution_time,
            )

            return {
                "name": self.name,
                "benchmark_passed": False,
                "duration": execution_time,
                "summary": {"error": "timeout", "execution_time": execution_time},
                "results": [],
                "metadata": {"execution_time": execution_time, "error": "timeout"},
            }

        # Analyze concurrent execution results
        successful_results = [
            r for r in results if not isinstance(r, Exception) and "Failed after" not in str(r)
        ]
        failed_results = [
            r for r in results if isinstance(r, Exception) or "Failed after" in str(r)
        ]

        # Validate expected content in successful results
        search_success = False
        shell_success = False
        calc_success = False

        if len(successful_results) >= 1:
            search_result = str(successful_results[0]).lower()
            search_success = any(
                word in search_result for word in ["python", "asyncio", "tutorial"]
            )

        if len(successful_results) >= 2:
            shell_result = str(successful_results[1]).lower()
            shell_success = "hello" in shell_result and "concurrent" in shell_result

        if len(successful_results) >= 3:
            calc_result = str(successful_results[2])
            calc_success = "352" in calc_result  # 15 * 23 + 7 = 352

        # Score concurrent execution quality
        all_completed = len(failed_results) == 0
        reasonable_time = execution_time < 45.0
        success_indicators = [search_success, shell_success, calc_success]
        success_count = sum(success_indicators)

        concurrent_score = success_count / len(success_indicators)

        # Judge concurrent execution quality
        combined_output = "\n\n".join([f"Task {i+1}: {result}" for i, result in enumerate(results)])
        judge_result = await self._evaluate_concurrent_response(
            tasks, combined_output, success_indicators, execution_time
        )

        # Log result
        self.logger.log_result(
            eval_name="concurrent_agent_execution",
            judge_result=judge_result,
            agent_metadata={
                "agents_count": len(agents),
                "successful_count": len(successful_results),
                "failed_count": len(failed_results),
                "execution_time": execution_time,
            },
            execution_time=time.time() - start_time,
        )

        test_passed = (
            all_completed
            and reasonable_time
            and concurrent_score >= 0.67
            and judge_result.score.value >= 6.0
        )

        duration = time.time() - start_time

        return {
            "name": self.name,
            "benchmark_passed": test_passed,
            "duration": duration,
            "summary": {
                "concurrent_score": concurrent_score,
                "all_completed": all_completed,
                "reasonable_time": reasonable_time,
                "judge_score": judge_result.score.value,
            },
            "results": [
                {
                    "scenario": "3-agent concurrent execution",
                    "tasks": tasks,
                    "execution_time": execution_time,
                    "successful_count": len(successful_results),
                    "failed_count": len(failed_results),
                    "judge_score": judge_result.score.value,
                    "judge_reasoning": judge_result.score.reasoning,
                    "passed": test_passed,
                    "task_results": {
                        "search_success": search_success,
                        "shell_success": shell_success,
                        "calc_success": calc_success,
                        "results": [
                            str(r)[:200] + "..." if len(str(r)) > 200 else str(r) for r in results
                        ],
                    },
                }
            ],
            "metadata": {
                "evaluation_focus": "concurrent_execution",
                "pattern_source": "archive/agent_concurrency.py",
                "agents_tested": len(agents),
                "resource_isolation": True,
                "logging_report": self.logger.generate_report(),
            },
        }

    async def _evaluate_concurrent_response(
        self, tasks: list, combined_output: str, success_indicators: list, execution_time: float
    ):
        """Evaluate concurrent execution quality."""

        successful_tasks = sum(success_indicators)

        criteria = f"""Concurrent Agent Execution Assessment:

Tasks: {len(tasks)} agents running in parallel
Successful Tasks: {successful_tasks}/{len(tasks)}
Execution Time: {execution_time:.2f}s

Rate the system's concurrent execution capabilities:

1. **Parallel Processing**: Did agents execute simultaneously without blocking?
2. **Resource Management**: Were tools and resources properly isolated between agents?
3. **Task Completion**: Did agents complete their assigned tasks successfully?
4. **Performance**: Was execution time reasonable for concurrent operations?
5. **Error Handling**: Were failures handled gracefully without affecting other agents?

Score 1-3: Poor concurrency, blocking or resource conflicts
Score 4-6: Partial concurrency with some successful parallel execution
Score 7-8: Good concurrent execution with proper resource management
Score 9-10: Excellent parallel processing with optimal resource isolation"""

        return await self.judge.evaluate(
            agent_response=combined_output,
            test_case=f"Concurrent execution of {len(tasks)} agents",
            criteria=criteria,
            context={
                "evaluation_focus": "concurrent_execution",
                "successful_tasks": successful_tasks,
                "total_tasks": len(tasks),
                "execution_time": execution_time,
            },
        )
