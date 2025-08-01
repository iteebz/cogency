"""SWE benchmark - Software engineering task completion."""

import json
from pathlib import Path

from cogency import Agent
from cogency.tools.code import Code
from evals.core.base import Eval, EvalResult


class SWE(Eval):
    """Test agent's ability to complete software engineering tasks."""

    name = "swe"
    description = "Software engineering task completion benchmark"

    def __init__(self):
        super().__init__()
        self.results_dir = Path("evals/results")
        self.results_dir.mkdir(exist_ok=True)

    async def run(self) -> EvalResult:
        """Run 3 hardcoded SWE tasks and aggregate results."""

        tasks = [
            {
                "id": "fix_bug_1",
                "prompt": "Fix this Python function that should return the sum of even numbers in a list:\n\ndef sum_evens(nums):\n    total = 0\n    for num in nums:\n        if num % 2 == 1:  # Bug here\n            total += num\n    return total\n\nReturn only the corrected function.",
                "expected_keywords": ["% 2 == 0", "even"],
            },
            {
                "id": "implement_feature_1",
                "prompt": "Write a Python function `merge_dicts(dict1, dict2)` that merges two dictionaries. If keys overlap, sum the values. Return only the function.",
                "expected_keywords": ["def merge_dicts", "dict1", "dict2", "+"],
            },
            {
                "id": "optimize_code_1",
                "prompt": "Optimize this O(n²) function to O(n):\n\ndef has_duplicates(arr):\n    for i in range(len(arr)):\n        for j in range(i+1, len(arr)):\n            if arr[i] == arr[j]:\n                return True\n    return False\n\nReturn only the optimized function.",
                "expected_keywords": ["set", "len(set(", "seen"],
            },
        ]

        agent = Agent("swe_tester", mode="reasoning", tools=[Code()])
        results = []

        for i, task in enumerate(tasks, 1):
            print(f"{i}/3 SWE tests...")

            try:
                response = await agent.run(task["prompt"])

                # Check if response contains expected patterns
                passed = all(
                    keyword.lower() in response.lower() for keyword in task["expected_keywords"]
                )

                score = 1.0 if passed else 0.0

                task_result = {
                    "task_id": task["id"],
                    "passed": passed,
                    "score": score,
                    "prompt": task["prompt"],
                    "response": response,
                    "expected_keywords": task["expected_keywords"],
                }

                results.append(task_result)

                # Log immediately
                self._log_task_result(task_result)

            except Exception as e:
                task_result = {
                    "task_id": task["id"],
                    "passed": False,
                    "score": 0.0,
                    "error": str(e),
                }
                results.append(task_result)
                self._log_task_result(task_result)

        # Aggregate results
        total_score = sum(r["score"] for r in results)
        avg_score = total_score / len(results)
        passed_count = sum(1 for r in results if r.get("passed", False))

        final_result = EvalResult(
            name=self.name,
            passed=avg_score >= 0.15,  # 15% pass rate target
            score=avg_score,
            duration=0.0,
            expected="Complete basic software engineering tasks",
            actual=f"{passed_count}/{len(results)} tasks completed",
            metadata={
                "tasks_completed": passed_count,
                "total_tasks": len(results),
                "individual_results": results,
            },
        )

        # Log final aggregated result
        self._log_final_result(final_result)

        return final_result

    def _log_task_result(self, task_result: dict):
        """Log individual task result."""
        timestamp = int(self.start_time) if self.start_time else 0
        log_file = self.results_dir / f"swe_task_{task_result['task_id']}_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(task_result, f, indent=2)

    def _log_final_result(self, result: EvalResult):
        """Log final aggregated result."""
        timestamp = int(self.start_time) if self.start_time else 0
        log_file = self.results_dir / f"swe_final_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
