"""Network resilience evaluation - canonical implementation."""

from typing import Any

from ..core import agent


class NetworkResilience:
    """Test agent resilience to network issues."""

    name = "network_resilience"
    description = "Network failure resilience"

    async def execute(self) -> dict[str, Any]:
        """Execute network resilience evaluation."""
        # Simple network test cases
        test_cases = [
            {
                "name": "basic_connectivity",
                "prompt": "What is 2+2?",
                "validator": lambda r: "4" in r,
            },
            {
                "name": "simple_reasoning",
                "prompt": "If I have 5 apples and give away 2, how many do I have?",
                "validator": lambda r: "3" in r,
            },
            {
                "name": "text_processing",
                "prompt": "Count the words in this sentence: 'Hello world test'",
                "validator": lambda r: "3" in r,
            },
        ]

        results = []
        for case in test_cases:
            test_agent = agent()

            try:
                response, _ = await test_agent.run(case["prompt"])
                passed = case["validator"](response)

                results.append(
                    {
                        "name": case["name"],
                        "prompt": case["prompt"],
                        "response": response[:100] + "..." if len(response) > 100 else response,
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
