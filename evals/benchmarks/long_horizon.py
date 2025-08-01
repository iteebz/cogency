"""LongHorizon stress test - Multi-step resilience with failure injection."""

import asyncio
import json
from pathlib import Path
from typing import Dict

from cogency import Agent
from cogency.tools.code import Code
from cogency.tools.search import Search
from evals.core.base import Eval, EvalResult


class LongHorizon(Eval):
    """Test agent resilience over extended multi-step workflows."""

    name = "long_horizon"
    description = "Multi-step workflow resilience stress test"

    def __init__(self):
        super().__init__()
        self.results_dir = Path("evals/results")
        self.results_dir.mkdir(exist_ok=True)

    async def run(self) -> EvalResult:
        """Run 3 long-horizon tasks with failure injection."""

        tasks = [
            {
                "id": "research_report",
                "prompt": "Research and create a brief report on Python async/await. Include: 1) What is async/await, 2) Basic example, 3) One key benefit. Make it 3 paragraphs total.",
                "steps": 10,
                "failure_points": [3, 7],  # Inject failures at these step counts
                "success_keywords": ["async", "await", "concurrency", "example", "benefit"],
            },
            {
                "id": "code_analysis",
                "prompt": "Analyze this code and suggest improvements:\n\ndef process_data(items):\n    result = []\n    for item in items:\n        if item > 0:\n            result.append(item * 2)\n    return result\n\nProvide 3 specific improvements with explanations.",
                "steps": 8,
                "failure_points": [4],
                "success_keywords": [
                    "list comprehension",
                    "improvement",
                    "performance",
                    "readable",
                ],
            },
            {
                "id": "multi_step_calculation",
                "prompt": "Calculate compound interest step by step: Principal=$1000, Rate=5%, Time=3 years. Show each year's calculation, then explain the concept of compounding in 2 sentences.",
                "steps": 6,
                "failure_points": [2, 5],
                "success_keywords": ["1000", "compound", "1157", "year", "interest"],
            },
        ]

        results = []

        for i, task in enumerate(tasks, 1):
            print(f"{i}/3 LongHorizon tests...")

            task_result = await self._run_resilience_test(task)
            results.append(task_result)
            self._log_task_result(task_result)

        # Aggregate results
        successful_tasks = sum(1 for r in results if r["completed_successfully"])
        avg_recovery_rate = sum(r["recovery_rate"] for r in results) / len(results)

        final_result = EvalResult(
            name=self.name,
            passed=avg_recovery_rate >= 0.8,  # >80% recovery rate target
            score=avg_recovery_rate,
            duration=0.0,
            expected="Successfully recover from failures in long workflows",
            actual=f"{successful_tasks}/{len(results)} tasks completed, {avg_recovery_rate:.1%} recovery rate",
            metadata={
                "successful_tasks": successful_tasks,
                "total_tasks": len(results),
                "average_recovery_rate": avg_recovery_rate,
                "individual_results": results,
            },
        )

        self._log_final_result(final_result)
        return final_result

    async def _run_resilience_test(self, task: Dict) -> Dict:
        """Run a single long-horizon task with failure injection."""
        agent = Agent("longhorizon_tester", mode="reasoning", tools=[Code(), Search()])

        failures_injected = 0
        recoveries_successful = 0
        step_count = 0
        final_response = ""

        try:
            # Simulate long workflow by breaking task into parts
            base_prompt = task["prompt"]

            for step in range(1, task["steps"] + 1):
                step_count = step

                # Inject failure at specified points
                if step in task["failure_points"]:
                    failures_injected += 1

                    # Simulate different failure types
                    failure_type = await self._inject_failure(step)

                    # Small delay to simulate failure recovery
                    await asyncio.sleep(0.2)

                    # Test recovery by continuing
                    try:
                        recovery_prompt = (
                            f"Continue with the previous task. Step {step} of the analysis."
                        )
                        response = await agent.run(recovery_prompt)
                        if response and len(response) > 20:  # Basic response validation
                            recoveries_successful += 1
                    except Exception:
                        pass  # Recovery failed
                else:
                    # Normal execution step
                    step_prompt = f"{base_prompt}\n\nFocus on step {step} of {task['steps']}."
                    try:
                        response = await agent.run(step_prompt)
                        final_response = response  # Keep last successful response
                    except Exception:
                        pass

                # Small delay between steps
                await asyncio.sleep(0.1)

            # Check final output quality
            success_indicators = sum(
                1
                for keyword in task["success_keywords"]
                if keyword.lower() in final_response.lower()
            )

            output_quality = success_indicators / len(task["success_keywords"])
            completed_successfully = output_quality >= 0.4  # At least 40% of expected content

            recovery_rate = (
                recoveries_successful / failures_injected if failures_injected > 0 else 1.0
            )

        except Exception as e:
            completed_successfully = False
            recovery_rate = 0.0
            final_response = f"Task failed: {e}"

        return {
            "task_id": task["id"],
            "completed_successfully": completed_successfully,
            "steps_completed": step_count,
            "total_steps": task["steps"],
            "failures_injected": failures_injected,
            "recoveries_successful": recoveries_successful,
            "recovery_rate": recovery_rate,
            "final_response": final_response[:500],  # Truncate for logging
            "success_keywords_found": success_indicators if "success_indicators" in locals() else 0,
        }

    async def _inject_failure(self, step: int) -> str:
        """Simulate different types of failures."""
        failure_types = [
            "memory_pressure",  # Simulate memory constraint
            "timeout_simulation",  # Simulate timeout
            "api_error_simulation",  # Simulate API failure
        ]

        failure_type = failure_types[step % len(failure_types)]

        if failure_type == "memory_pressure":
            # Simulate memory pressure by creating temporary objects
            temp_data = ["x" * 1000 for _ in range(100)]
            await asyncio.sleep(0.1)
            del temp_data

        elif failure_type == "timeout_simulation":
            # Simulate timeout with delay
            await asyncio.sleep(0.3)

        elif failure_type == "api_error_simulation":
            # Simulate API failure with exception (caught by caller)
            if step % 4 == 0:  # Occasionally raise exception
                raise Exception("Simulated API failure")

        return failure_type

    def _log_task_result(self, task_result: dict):
        """Log individual task result."""
        timestamp = int(self.start_time) if self.start_time else 0
        log_file = self.results_dir / f"longhorizon_task_{task_result['task_id']}_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(task_result, f, indent=2)

    def _log_final_result(self, result: EvalResult):
        """Log final aggregated result."""
        timestamp = int(self.start_time) if self.start_time else 0
        log_file = self.results_dir / f"longhorizon_final_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
