"""Reading comprehension and logical reasoning evaluation."""

import asyncio

from cogency import Agent
from cogency.tools.search import Search

from ...core import Eval, EvalResult


class Comprehension(Eval):
    """Test agent's reasoning and comprehension capabilities."""

    name = "comprehension"
    description = "Elementary logic, math, and comprehension tasks"

    async def run(self) -> EvalResult:
        tasks = [
            {
                "id": "math_word_problem",
                "prompt": "If a train travels 120 miles in 2 hours, then speeds up and travels 180 miles in the next 1.5 hours, what is its average speed for the entire journey?",
                "expected_keywords": ["average", "total", "miles", "hours", "85", "86"],
            },
            {
                "id": "logical_reasoning",
                "prompt": "All cats are mammals. Some mammals are dogs. Therefore, some cats are dogs. Is this conclusion valid? Explain in one sentence.",
                "expected_keywords": ["invalid", "false", "incorrect", "not valid", "fallacy"],
            },
            {
                "id": "reading_comprehension",
                "prompt": "Text: 'The library opens at 9 AM on weekdays and 10 AM on weekends. It closes at 8 PM Monday through Thursday, 6 PM on Friday, and 5 PM on weekends.' Question: If today is Wednesday, how many hours is the library open?",
                "expected_keywords": ["9", "8", "11", "hours"],
            },
        ]

        agent = Agent("comprehension_tester", mode="reasoning", tools=[Search()], robust=False)
        results = []

        for task in tasks:
            try:
                response = await asyncio.wait_for(agent.run(task["prompt"]), timeout=30)
                response_lower = response.lower()

                # Check for expected reasoning keywords
                keywords_found = sum(
                    1 for keyword in task["expected_keywords"] if keyword.lower() in response_lower
                )

                # Scoring: full credit if most keywords found
                if keywords_found >= len(task["expected_keywords"]) // 2:
                    score = 1.0
                    passed = True
                elif keywords_found > 0:
                    score = 0.5
                    passed = False
                else:
                    score = 0.0
                    passed = False

                results.append(
                    {
                        "task_id": task["id"],
                        "passed": passed,
                        "score": score,
                        "keywords_found": keywords_found,
                        "response": response,
                    }
                )

            except asyncio.TimeoutError:
                results.append(
                    {
                        "task_id": task["id"],
                        "passed": False,
                        "score": 0.0,
                        "error": "timeout",
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "task_id": task["id"],
                        "passed": False,
                        "score": 0.0,
                        "error": str(e),
                    }
                )

        # Aggregate results
        total_score = sum(r["score"] for r in results)
        avg_score = total_score / len(results)
        passed_count = sum(1 for r in results if r.get("passed", False))

        return EvalResult(
            name=self.name,
            passed=avg_score >= 0.5,  # 50% pass rate target
            score=avg_score,
            duration=0.0,  # Will be set by base class
            expected="Complete reasoning and comprehension tasks",
            actual=f"{passed_count}/{len(results)} tasks passed",
            metadata={"individual_results": results},
        )
