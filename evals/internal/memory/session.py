"""Cross-session memory evaluation - canonical implementation."""

from typing import Any

from ...core import agent, memory_tests, tests


class SessionMemory:
    """Test memory persistence across sessions."""

    name = "cross_session_memory"
    description = "Cross-session memory persistence"

    async def execute(self) -> dict[str, Any]:
        """Execute cross-session memory evaluation."""
        test_cases = memory_tests(tests("memory"))

        results = []
        for case in test_cases:
            # Use same user_id for both sessions - memory is user-scoped, not agent-scoped
            user_id = f"memory_test_{case['name']}"

            # Session 1: Store information with memory enabled
            store_agent = agent(memory=True)
            try:
                await store_agent.run(case["store_prompt"], user_id=user_id)

                # Session 2: Recall information (new agent instance, same user_id)
                recall_agent = agent(memory=True)
                response, _ = await recall_agent.run(case["recall_prompt"], user_id=user_id)

                passed = case["validator"](response)

                results.append(
                    {
                        "name": case["name"],
                        "store_prompt": case["store_prompt"],
                        "recall_prompt": case["recall_prompt"],
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "passed": passed,
                    }
                )
            except Exception as e:
                results.append({"name": case["name"], "error": str(e), "passed": False})

        passed = sum(1 for r in results if r.get("passed", False))

        return {
            "name": self.name,
            "results": results,
            "summary": {
                "total": len(results),
                "passed": passed,
                "rate": passed / len(results) if results else 0,
                "benchmark_passed": passed == len(results),
            },
        }
