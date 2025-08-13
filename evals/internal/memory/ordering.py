"""Temporal ordering evaluation - canonical implementation."""

from typing import Any

from ...core import agent


class MemoryOrdering:
    """Test temporal sequence memory and ordering."""

    name = "temporal_ordering"
    description = "Temporal sequence and ordering memory"

    async def execute(self) -> dict[str, Any]:
        """Execute temporal ordering evaluation."""
        test_cases = [
            {
                "name": "sequence_recall",
                "setup_prompts": [
                    "First, I told you about Project Alpha",
                    "Then, I mentioned Project Beta",
                    "Finally, I discussed Project Gamma",
                ],
                "test_prompt": "What was the first project I mentioned?",
                "validator": lambda r: "alpha" in r.lower(),
            },
            {
                "name": "temporal_order",
                "setup_prompts": [
                    "At 9am I had coffee",
                    "At 10am I had a meeting",
                    "At 11am I wrote code",
                ],
                "test_prompt": "What did I do at 10am?",
                "validator": lambda r: "meeting" in r.lower(),
            },
        ]

        results = []
        for case in test_cases:
            temporal_agent = agent()

            try:
                # Setup sequence
                for prompt in case["setup_prompts"]:
                    await temporal_agent.run(prompt)

                # Test recall
                response, _ = await temporal_agent.run(case["test_prompt"])
                passed = case["validator"](response)

                results.append(
                    {
                        "name": case["name"],
                        "test_prompt": case["test_prompt"],
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
