"""Adaptive modes evaluation - canonical implementation."""

from typing import Any

from ..core import agent


class AdaptiveModes:
    """Test agent mode switching capabilities."""

    name = "adaptive_modes"
    description = "Mode switching and adaptation"

    async def execute(self) -> dict[str, Any]:
        """Execute adaptive modes evaluation."""
        test_cases = [
            {
                "name": "fast_mode_simple",
                "prompt": "What is 10+5?",
                "mode": "fast",
                "validator": lambda r: "15" in r,
            },
            {
                "name": "deep_mode_analysis",
                "prompt": "Analyze the pros and cons of renewable energy",
                "mode": "deep",
                "validator": lambda r: len(r) > 100,
            },
            {
                "name": "creative_mode_story",
                "prompt": "Write a short story about a robot",
                "mode": "creative",
                "validator": lambda r: len(r) > 50,
            },
        ]

        results = []
        for case in test_cases:
            # Create agent with specific mode
            mode_agent = agent()
            mode_agent.mode = case["mode"]

            try:
                response, _ = await mode_agent.run(case["prompt"])
                passed = case["validator"](response)

                results.append(
                    {
                        "name": case["name"],
                        "mode": case["mode"],
                        "prompt": case["prompt"],
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
