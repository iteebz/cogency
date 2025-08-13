"""Workflow orchestration evaluation - canonical implementation."""

from typing import Any

from ..core import agent, tests, workflow_tests


class WorkflowOrchestration:
    """Test complex multi-tool workflow orchestration."""

    name = "workflow_orchestration"
    description = "Complex multi-step workflows"

    async def execute(self) -> dict[str, Any]:
        """Execute workflow evaluation."""
        test_cases = workflow_tests(tests("workflows"))

        results = []
        for case in test_cases:
            workflow_agent = agent()
            workflow_agent.tools = case["tools"]

            try:
                response, _ = await workflow_agent.run(case["prompt"])
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
