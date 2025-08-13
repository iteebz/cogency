"""Production resilience evaluation - error handling and recovery."""

import time
from typing import Any

from ..core import agent


class ProductionResilience:
    """Test production-ready resilience and error recovery."""

    name = "production_resilience"
    description = "Error handling and recovery"
    time_budget = 300
    pass_threshold = 0.6

    def __init__(self):
        self.resilience_tests = [
            {
                "name": "file_not_found_recovery",
                "prompt": "Read 'nonexistent.txt' and handle the error gracefully",
                "validator": lambda r: any(
                    word in r.lower() for word in ["not found", "error", "doesn't exist"]
                ),
                "essential": True,
            },
            {
                "name": "permission_denied_handling",
                "prompt": "Try to write to '/root/protected.txt' and handle permission errors",
                "validator": lambda r: any(
                    word in r.lower() for word in ["permission", "denied", "error"]
                ),
                "essential": True,
            },
            {
                "name": "command_not_found_recovery",
                "prompt": "Run 'nonexistent_command --help' and handle the error",
                "validator": lambda r: any(
                    word in r.lower() for word in ["not found", "command", "error"]
                ),
                "essential": True,
            },
            {
                "name": "network_unavailable_handling",
                "prompt": "Search for 'latest AI news' and handle network issues if they occur",
                "validator": lambda r: len(r) > 10,  # Any reasonable response
                "essential": False,
            },
            {
                "name": "malformed_data_recovery",
                "prompt": "Parse this invalid JSON: '{invalid json}' and handle the error",
                "validator": lambda r: any(
                    word in r.lower() for word in ["invalid", "json", "error", "parse"]
                ),
                "essential": True,
            },
        ]

    async def execute(self) -> dict[str, Any]:
        """Execute resilience evaluation."""
        print("🛡️ Production Resilience")
        start_time = time.time()

        test_agent = agent()
        results = []
        passed_tests = 0
        critical_failures = 0

        for test_case in self.resilience_tests:
            print(f"  Testing: {test_case['name']}")

            try:
                response, _ = await test_agent.run(test_case["prompt"])
                passed = test_case["validator"](response)

                if passed:
                    passed_tests += 1
                elif test_case["essential"]:
                    critical_failures += 1

                results.append(
                    {
                        "name": test_case["name"],
                        "prompt": test_case["prompt"],
                        "response": response[:150] + "..." if len(response) > 150 else response,
                        "passed": passed,
                        "essential": test_case["essential"],
                    }
                )

                status = "✅" if passed else "❌"
                essential_flag = "🔴" if test_case["essential"] and not passed else ""
                print(f"    {status} {essential_flag} {test_case['name']}")

            except Exception as e:
                if test_case["essential"]:
                    critical_failures += 1
                results.append(
                    {
                        "name": test_case["name"],
                        "error": str(e),
                        "passed": False,
                        "essential": test_case["essential"],
                    }
                )
                print(f"    💥 {test_case['name']}: {e}")

        duration = time.time() - start_time
        pass_rate = passed_tests / len(self.resilience_tests)
        resilience_solid = pass_rate >= self.pass_threshold and critical_failures == 0

        # Generate insight
        if critical_failures > 0:
            insight = f"Critical: {critical_failures} essential resilience failures"
        elif pass_rate >= 0.8:
            insight = "Exceptional: production-ready error handling"
        elif pass_rate >= 0.6:
            insight = "Solid: adequate error recovery mechanisms"
        else:
            insight = f"Insufficient: only {pass_rate:.1%} resilience working"

        return {
            "name": self.name,
            "tier": "production",
            "resilience_solid": resilience_solid,
            "duration": duration,
            "summary": {
                "total_tests": len(self.resilience_tests),
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "critical_failures": critical_failures,
                "production_ready": resilience_solid,
            },
            "results": results,
            "executive_insight": insight,
            "recommendation": "PRODUCTION_READY" if resilience_solid else "NEEDS_HARDENING",
        }
