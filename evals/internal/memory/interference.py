"""Memory interference evaluation - canonical implementation."""

from typing import Any

from ...core import agent


class MemoryInterference:
    """Test memory isolation between different sessions."""

    name = "memory_interference"
    description = "Memory isolation and interference testing"

    async def execute(self) -> dict[str, Any]:
        """Execute memory interference evaluation."""
        test_cases = [
            {
                "name": "session_isolation",
                "user1_prompt": "Remember: My favorite color is blue",
                "user2_prompt": "What is my favorite color?",
                "validator": lambda r: "don't know" in r.lower() or "no information" in r.lower(),
            },
            {
                "name": "context_separation",
                "session1_prompt": "My project is called Phoenix",
                "session2_prompt": "What project am I working on?",
                "validator": lambda r: "don't" in r.lower() or "no project" in r.lower(),
            },
        ]

        results = []
        for case in test_cases:
            # Test user isolation - different user_ids should not share memory
            user1_id = f"user1_{case['name']}"
            user2_id = f"user2_{case['name']}"

            agent1 = agent(memory=True)
            agent2 = agent(memory=True)

            try:
                # User 1 stores information
                await agent1.run(
                    case.get("user1_prompt", case.get("session1_prompt", "")), user_id=user1_id
                )

                # User 2 tries to access it (should fail - different user_id)
                response, _ = await agent2.run(
                    case.get("user2_prompt", case.get("session2_prompt", "")), user_id=user2_id
                )
                passed = case["validator"](response)

                results.append(
                    {
                        "name": case["name"],
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
