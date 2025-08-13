"""Comprehensive tool integration - all available tools tested."""

import time
from typing import Any

from ..core import agent


class ComprehensiveTools:
    """Test all available Cogency tools."""

    name = "comprehensive_tools"
    description = "Files, Search, Scrape, Retrieve, Shell"
    time_budget = 120
    pass_threshold = 0.8

    def __init__(self):
        self.tool_tests = [
            # Files tool
            {
                "name": "files_create_read",
                "prompt": "Create a file called 'test.md' with content '# Test' and then read it back",
                "validator": lambda r: "test" in r.lower() and "#" in r,
                "tools_required": ["files"],
                "essential": True,
            },
            # Shell tool
            {
                "name": "shell_basic_command",
                "prompt": "Run 'echo Hello Tools' using shell command",
                "validator": lambda r: "hello tools" in r.lower(),
                "tools_required": ["shell"],
                "essential": True,
            },
            # Search tool
            {
                "name": "search_web_query",
                "prompt": "Search for 'Python async programming' and summarize findings",
                "validator": lambda r: any(
                    word in r.lower() for word in ["async", "python", "search"]
                ),
                "tools_required": ["search"],
                "essential": True,
            },
            # Scrape tool
            {
                "name": "scrape_web_content",
                "prompt": "Scrape content from 'https://python.org' homepage",
                "validator": lambda r: "python" in r.lower(),
                "tools_required": ["scrape"],
                "essential": True,
            },
            # Retrieve tool
            {
                "name": "retrieve_documents",
                "prompt": "Retrieve relevant documents about 'machine learning basics'",
                "validator": lambda r: len(r) > 20,  # Any substantial response
                "tools_required": ["retrieve"],
                "essential": False,  # May not have documents indexed
            },
            # Recall tool
            {
                "name": "recall_memory",
                "prompt": "Remember this: 'My favorite color is blue' then recall what I just told you",
                "validator": lambda r: "blue" in r.lower(),
                "tools_required": ["recall"],
                "essential": True,
            },
            # Multi-tool workflow
            {
                "name": "multi_tool_workflow",
                "prompt": "Search for Python news, save results to a file, then read the file back",
                "validator": lambda r: any(
                    word in r.lower() for word in ["python", "file", "search"]
                ),
                "tools_required": ["search", "files"],
                "essential": True,
            },
            # Tool orchestration
            {
                "name": "tool_orchestration",
                "prompt": "Create a research project: search for AI trends, scrape a relevant page, and summarize findings in a file",
                "validator": lambda r: any(
                    word in r.lower() for word in ["ai", "trends", "summary"]
                ),
                "tools_required": ["search", "scrape", "files"],
                "essential": True,
            },
        ]

    async def execute(self) -> dict[str, Any]:
        """Execute comprehensive tool evaluation."""
        print("🛠️ Comprehensive Tools")
        print("Testing: Files, Search, Scrape, Retrieve, Shell, Recall")
        start_time = time.time()

        # Create agent with all tools
        test_agent = agent()
        # Enable all available tools
        test_agent.tools = ["files", "shell", "search", "scrape", "retrieve", "recall"]

        results = []
        passed_tests = 0
        critical_failures = 0
        tool_availability = {}

        for test_case in self.tool_tests:
            print(f"  Testing: {test_case['name']}")

            try:
                response, _ = await test_agent.run(test_case["prompt"])
                passed = test_case["validator"](response)

                if passed:
                    passed_tests += 1
                elif test_case["essential"]:
                    critical_failures += 1

                # Track tool availability
                for tool in test_case["tools_required"]:
                    if tool not in tool_availability:
                        tool_availability[tool] = {"used": 0, "successful": 0}
                    tool_availability[tool]["used"] += 1
                    if passed:
                        tool_availability[tool]["successful"] += 1

                results.append(
                    {
                        "name": test_case["name"],
                        "prompt": test_case["prompt"],
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "passed": passed,
                        "tools_required": test_case["tools_required"],
                        "essential": test_case["essential"],
                    }
                )

                status = "✅" if passed else "❌"
                tools_str = "+".join(test_case["tools_required"])
                print(f"    {status} {test_case['name']} ({tools_str})")

            except Exception as e:
                if test_case["essential"]:
                    critical_failures += 1
                results.append(
                    {
                        "name": test_case["name"],
                        "error": str(e),
                        "passed": False,
                        "tools_required": test_case["tools_required"],
                        "essential": test_case["essential"],
                    }
                )
                print(f"    💥 {test_case['name']}: {e}")

        duration = time.time() - start_time
        pass_rate = passed_tests / len(self.tool_tests)
        tools_comprehensive = pass_rate >= self.pass_threshold and critical_failures == 0

        # Calculate tool success rates
        tool_success_rates = {}
        for tool, stats in tool_availability.items():
            tool_success_rates[tool] = (
                stats["successful"] / stats["used"] if stats["used"] > 0 else 0.0
            )

        # Generate insight
        working_tools = sum(1 for rate in tool_success_rates.values() if rate > 0.5)
        total_tools = len(tool_success_rates)

        if critical_failures > 0:
            insight = f"Critical: {critical_failures} essential tool failures"
        elif pass_rate >= 0.9 and working_tools >= 5:
            insight = f"Exceptional: {working_tools}/{total_tools} tools working perfectly"
        elif pass_rate >= 0.8:
            insight = f"Strong: {working_tools}/{total_tools} tools operational"
        else:
            insight = f"Limited: only {working_tools}/{total_tools} tools working reliably"

        return {
            "name": self.name,
            "tier": "foundation",
            "tools_comprehensive": tools_comprehensive,
            "duration": duration,
            "summary": {
                "total_tests": len(self.tool_tests),
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "critical_failures": critical_failures,
                "working_tools": working_tools,
                "total_tools_tested": total_tools,
                "tool_success_rates": tool_success_rates,
                "comprehensive_tooling": tools_comprehensive,
            },
            "results": results,
            "executive_insight": insight,
            "recommendation": "CONTINUE_EVALUATION" if tools_comprehensive else "TOOL_LIMITATIONS",
        }
