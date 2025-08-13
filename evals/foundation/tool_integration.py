"""Basic tool usage - files and shell commands."""

import time
from typing import Any

from ..core import agent


class ToolIntegration:
    """Test basic tool usage."""

    name = "tool_integration"
    description = "Files and shell commands"
    time_budget = 45
    pass_threshold = 0.9

    def __init__(self):
        self.canonical_tests = [
            {
                "name": "file_creation",
                "prompt": "Create a file called 'test.txt' with the content 'Hello Foundation'",
                "validator": self._validate_file_created,
                "essential": True,
            },
            {
                "name": "file_reading",
                "prompt": "Read the contents of the file 'test.txt' you just created",
                "validator": lambda r: "Hello Foundation" in r,
                "essential": True,
            },
            {
                "name": "simple_command",
                "prompt": "Run the command 'echo Foundation Test'",
                "validator": lambda r: "Foundation Test" in r,
                "essential": True,
            },
            {
                "name": "directory_listing",
                "prompt": "List the files in the current directory",
                "validator": lambda r: "test.txt" in r
                or any(word in r.lower() for word in ["file", "directory", "ls"]),
                "essential": True,
            },
            {
                "name": "file_modification",
                "prompt": "Add the line 'Tool test complete' to the test.txt file",
                "validator": lambda r: "complete" in r.lower() or "added" in r.lower(),
                "essential": True,
            },
            {
                "name": "command_with_output",
                "prompt": "Run 'pwd' to show current directory",
                "validator": lambda r: "/" in r,  # Path separator indicates directory output
                "essential": True,
            },
            {
                "name": "file_deletion",
                "prompt": "Delete the test.txt file",
                "validator": lambda r: any(
                    word in r.lower() for word in ["delete", "remove", "rm"]
                ),
                "essential": False,  # Cleanup, not essential
            },
            {
                "name": "tool_error_handling",
                "prompt": "Try to read a file called 'nonexistent_file.txt'",
                "validator": lambda r: any(
                    word in r.lower() for word in ["not found", "error", "exist", "no such"]
                ),
                "essential": True,
            },
            {
                "name": "multiple_commands",
                "prompt": "Create a file called 'multi.txt', write 'test' to it, then show its contents",
                "validator": lambda r: "test" in r,
                "essential": True,
            },
            {
                "name": "basic_shell_navigation",
                "prompt": "Show me what's in the current directory using ls or similar command",
                "validator": lambda r: len(r.strip()) > 0,  # Any output indicates tool usage
                "essential": True,
            },
        ]

    def _validate_file_created(self, response: str) -> bool:
        """Validate that file creation was attempted/mentioned."""
        indicators = ["created", "file", "test.txt", "hello foundation", "wrote", "saved"]
        return any(indicator in response.lower() for indicator in indicators)

    async def execute(self) -> dict[str, Any]:
        """Execute tool integration evaluation."""
        print("🛠️ Tool Integration")
        start_time = time.time()

        # Create agent with basic tools
        test_agent = agent()
        test_agent.tools = ["files", "shell"]

        results = []
        passed_tests = 0
        critical_failures = 0

        for test_case in self.canonical_tests:
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
        pass_rate = passed_tests / len(self.canonical_tests)
        tools_functional = pass_rate >= self.pass_threshold and critical_failures == 0

        # Generate insight
        if critical_failures > 0:
            insight = f"Critical: {critical_failures} essential tool operations failed"
        elif pass_rate >= 0.95:
            insight = "Solid: all basic tool operations confirmed"
        elif pass_rate >= 0.9:
            insight = "Adequate: core tool functionality working"
        else:
            insight = f"Insufficient: only {pass_rate:.1%} tool functionality working"

        return {
            "name": self.name,
            "tier": "foundation",
            "tools_functional": tools_functional,
            "duration": duration,
            "summary": {
                "total_tests": len(self.canonical_tests),
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "critical_failures": critical_failures,
                "tool_integration_viable": tools_functional,
            },
            "results": results,
            "executive_insight": insight,
            "recommendation": "CONTINUE_EVALUATION" if tools_functional else "TERMINATE_EVALUATION",
        }
