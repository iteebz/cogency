"""Tool chaining evaluation - canonical implementation."""

from typing import Any

from ..core import agent


class ToolChaining:
    """Test sequential tool usage and chaining."""

    name = "tool_chaining"
    description = "Sequential tool chaining"

    async def execute(self) -> dict[str, Any]:
        """Execute tool chaining evaluation."""
        from cogency.tools import Files, Shell

        test_cases = [
            {
                "name": "file_then_shell",
                "prompt": "Create file 'chain.txt' with 'test data', then use shell to count its lines",
                "tools": [Files(), Shell()],
                "validator": lambda r: "1" in r,  # Should have 1 line
            },
            {
                "name": "multi_file_ops",
                "prompt": "Create 'temp1.txt' and 'temp2.txt' with different content, then list both files",
                "tools": [Files(), Shell()],
                "validator": lambda r: "temp1" in r and "temp2" in r,
            },
            {
                "name": "create_execute_cleanup",
                "prompt": "Create script 'hello.py' with print('hello'), run it, then delete the file",
                "tools": [Files(), Shell()],
                "validator": lambda r: "hello" in r.lower(),
            },
        ]

        results = []
        for case in test_cases:
            chain_agent = agent()
            chain_agent.tools = case["tools"]

            try:
                response, _ = await chain_agent.run(case["prompt"])
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
