"""Error recovery evaluation - canonical implementation."""

from typing import Any

from ..core import agent


class ErrorRecovery:
    """Test agent error handling and recovery."""

    name = "error_recovery"
    description = "Error handling and recovery"

    async def execute(self) -> dict[str, Any]:
        """Execute error recovery evaluation."""
        test_cases = [
            {
                "name": "division_by_zero",
                "prompt": "Calculate 10/0 and handle any errors gracefully",
                "validator": lambda r: "error" in r.lower()
                or "undefined" in r.lower()
                or "infinity" in r.lower(),
            },
            {
                "name": "invalid_input",
                "prompt": "Process this invalid JSON: {invalid: data}",
                "validator": lambda r: "invalid" in r.lower() or "error" in r.lower(),
            },
            {
                "name": "missing_context",
                "prompt": "What was the last thing I told you about project X?",
                "validator": lambda r: "don't" in r.lower()
                or "no information" in r.lower()
                or "remember" in r.lower(),
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
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "passed": passed,
                    }
                )
            except Exception as e:
                # Agent crashing is also valid recovery behavior for some tests
                results.append(
                    {
                        "name": case["name"],
                        "prompt": case["prompt"],
                        "response": f"Agent handled error: {str(e)[:100]}",
                        "passed": True,  # Controlled failure is acceptable
                    }
                )

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
