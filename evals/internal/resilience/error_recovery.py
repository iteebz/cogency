"""Agent resilience and error recovery evaluation.

Tests how well Cogency handles various failure scenarios and recovers gracefully.
This demonstrates production-ready robustness for AGI lab evaluation.
"""

import time
from typing import Any

from ...core import agent


class ErrorRecoveryResilience:
    """Test agent resilience and error recovery capabilities."""

    name = "error_recovery_resilience"
    description = "Agent error recovery and resilience testing"

    def __init__(self, sample_size: int = 15):
        """Initialize with 15 error recovery scenarios."""
        self.sample_size = sample_size
        self.error_scenarios = self._create_error_scenarios()

    def _create_error_scenarios(self) -> list[dict[str, Any]]:
        """Create realistic error recovery test scenarios."""
        return [
            # File System Error Recovery
            {
                "name": "file_not_found_recovery",
                "category": "filesystem_errors",
                "description": "Handle missing files gracefully",
                "prompt": "Read the contents of 'nonexistent_file.txt' and if it doesn't exist, create it with some sample data, then read it again to verify.",
                "error_type": "FileNotFoundError",
                "recovery_strategy": "create_fallback_then_retry",
                "validator": lambda r: all(
                    keyword in r.lower() for keyword in ["create", "sample", "verify"]
                ),
                "expected_behavior": "graceful_handling_with_recovery",
            },
            {
                "name": "permission_denied_handling",
                "category": "filesystem_errors",
                "description": "Handle permission errors with alternatives",
                "prompt": "Try to write to '/root/protected_file.txt' and if permission is denied, create the file in the current directory instead with the same content.",
                "error_type": "PermissionError",
                "recovery_strategy": "alternative_path_fallback",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["current directory", "alternative", "instead"]
                ),
                "expected_behavior": "fallback_to_alternative",
            },
            {
                "name": "disk_space_simulation",
                "category": "filesystem_errors",
                "description": "Handle disk space limitations",
                "prompt": "Create a large file with random data, and if you encounter disk space issues, create a smaller file instead and explain the limitation.",
                "error_type": "OSError",
                "recovery_strategy": "resource_constrained_fallback",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["smaller", "limitation", "space"]
                ),
                "expected_behavior": "adaptive_resource_usage",
            },
            # Command Execution Error Recovery
            {
                "name": "command_not_found_recovery",
                "category": "command_errors",
                "description": "Handle missing commands gracefully",
                "prompt": "Run the command 'nonexistent_command --help' and if it fails, suggest alternative approaches or explain what might have been intended.",
                "error_type": "CommandNotFoundError",
                "recovery_strategy": "suggest_alternatives",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["alternative", "suggest", "intended"]
                ),
                "expected_behavior": "helpful_error_explanation",
            },
            {
                "name": "timeout_recovery",
                "category": "command_errors",
                "description": "Handle command timeouts",
                "prompt": "Run a command that might take a long time like 'sleep 100' and if it times out or you need to cancel it, explain what happened and suggest a shorter alternative.",
                "error_type": "TimeoutError",
                "recovery_strategy": "timeout_with_explanation",
                "validator": lambda r: any(
                    keyword in r.lower()
                    for keyword in ["timeout", "cancel", "shorter", "alternative"]
                ),
                "expected_behavior": "timeout_awareness_and_recovery",
            },
            {
                "name": "syntax_error_recovery",
                "category": "command_errors",
                "description": "Recover from command syntax errors",
                "prompt": "Run the command 'ls -invalid_flag_xyz' and when it fails, correct the command and try again with valid flags.",
                "error_type": "SyntaxError",
                "recovery_strategy": "syntax_correction_and_retry",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["correct", "valid", "try again"]
                ),
                "expected_behavior": "error_correction_and_retry",
            },
            # Network and External Service Errors
            {
                "name": "network_unavailable_handling",
                "category": "network_errors",
                "description": "Handle network unavailability",
                "prompt": "Try to search for information about 'latest Python releases' and if network/search is unavailable, provide what information you can from your training data instead.",
                "error_type": "NetworkError",
                "recovery_strategy": "fallback_to_local_knowledge",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["training", "knowledge", "available"]
                ),
                "expected_behavior": "graceful_degradation",
            },
            {
                "name": "api_rate_limit_handling",
                "category": "network_errors",
                "description": "Handle API rate limiting",
                "prompt": "Make multiple search requests quickly and if you hit rate limits, explain the limitation and suggest spacing out requests or alternative approaches.",
                "error_type": "RateLimitError",
                "recovery_strategy": "rate_limit_awareness",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["rate limit", "spacing", "alternative"]
                ),
                "expected_behavior": "rate_limit_management",
            },
            # Workflow Interruption Recovery
            {
                "name": "multi_step_interruption_recovery",
                "category": "workflow_errors",
                "description": "Recover from mid-workflow failures",
                "prompt": "Start creating a Python project with multiple files, then simulate a failure halfway through by trying to create a file with an invalid name '><invalid.py'. Handle the error and complete the project with valid filenames.",
                "error_type": "WorkflowInterruption",
                "recovery_strategy": "workflow_continuation_after_error",
                "validator": lambda r: all(
                    keyword in r.lower() for keyword in ["handle", "complete", "valid"]
                ),
                "expected_behavior": "workflow_resilience",
            },
            {
                "name": "dependency_missing_recovery",
                "category": "workflow_errors",
                "description": "Handle missing dependencies gracefully",
                "prompt": "Create a Python script that uses a library like 'nonexistent_lib'. When the import fails, modify the script to work without that dependency or suggest installation steps.",
                "error_type": "ImportError",
                "recovery_strategy": "dependency_fallback_or_guidance",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["modify", "without", "install"]
                ),
                "expected_behavior": "dependency_management",
            },
            # Resource Constraint Handling
            {
                "name": "memory_constraint_adaptation",
                "category": "resource_errors",
                "description": "Adapt to memory constraints",
                "prompt": "Process a large dataset but if you encounter memory issues, break it into smaller chunks or suggest memory-efficient alternatives.",
                "error_type": "MemoryError",
                "recovery_strategy": "chunked_processing_fallback",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["chunk", "smaller", "memory", "efficient"]
                ),
                "expected_behavior": "resource_efficient_adaptation",
            },
            {
                "name": "concurrent_resource_conflict",
                "category": "resource_errors",
                "description": "Handle resource conflicts",
                "prompt": "Try to write to a file that might be locked by another process. If it fails, wait and retry or use an alternative filename.",
                "error_type": "ResourceBusy",
                "recovery_strategy": "retry_with_backoff_or_alternative",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["wait", "retry", "alternative"]
                ),
                "expected_behavior": "conflict_resolution",
            },
            # Data Validation and Format Errors
            {
                "name": "malformed_data_recovery",
                "category": "data_errors",
                "description": "Handle malformed data gracefully",
                "prompt": "Try to parse JSON data: '{invalid json format with missing quotes and commas}'. When it fails, clean up the format and try again.",
                "error_type": "JSONDecodeError",
                "recovery_strategy": "data_cleaning_and_retry",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["clean", "format", "try again"]
                ),
                "expected_behavior": "data_recovery_attempt",
            },
            {
                "name": "encoding_error_handling",
                "category": "data_errors",
                "description": "Handle text encoding issues",
                "prompt": "Read a file that might have encoding issues and if you encounter encoding errors, try alternative encodings or error handling strategies.",
                "error_type": "UnicodeDecodeError",
                "recovery_strategy": "encoding_fallback_strategies",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["encoding", "alternative", "strategy"]
                ),
                "expected_behavior": "encoding_resilience",
            },
            # Context and State Recovery
            {
                "name": "context_corruption_recovery",
                "category": "state_errors",
                "description": "Recover from corrupted context",
                "prompt": "Start a complex calculation, then mention that there might be context issues. Reset and restart the calculation with clear intermediate steps to ensure accuracy.",
                "error_type": "ContextCorruption",
                "recovery_strategy": "context_reset_and_restart",
                "validator": lambda r: any(
                    keyword in r.lower() for keyword in ["reset", "restart", "clear", "steps"]
                ),
                "expected_behavior": "context_management",
            },
        ]

    async def execute(self) -> dict[str, Any]:
        """Execute error recovery resilience evaluation."""
        print("🛡️ Testing Error Recovery & Resilience - Production Readiness")
        start_time = time.time()

        # Use all scenarios or sample them
        selected_scenarios = self.error_scenarios[: self.sample_size]

        results = []
        passed_tests = 0
        recovery_success_count = 0

        for i, scenario in enumerate(selected_scenarios):
            print(f"Resilience ({i+1}/{len(selected_scenarios)}): {scenario['name']}")

            try:
                # Create agent with error recovery capabilities
                resilient_agent = agent()
                resilient_agent.tools = ["files", "shell", "search"]
                resilient_agent.max_iterations = 15  # Allow recovery attempts

                # Execute the scenario that's designed to trigger errors
                response, conversation_id = await resilient_agent.run(scenario["prompt"])

                # Validate error handling and recovery
                handled_gracefully = scenario["validator"](response)

                # Check for signs of recovery attempts
                recovery_indicators = [
                    "error" in response.lower() and "handle" in response.lower(),
                    "try" in response.lower() or "attempt" in response.lower(),
                    "alternative" in response.lower() or "instead" in response.lower(),
                    "fallback" in response.lower() or "backup" in response.lower(),
                ]

                recovery_attempted = any(recovery_indicators)

                if handled_gracefully:
                    passed_tests += 1

                if recovery_attempted:
                    recovery_success_count += 1

                results.append(
                    {
                        "name": scenario["name"],
                        "category": scenario["category"],
                        "error_type": scenario["error_type"],
                        "recovery_strategy": scenario["recovery_strategy"],
                        "expected_behavior": scenario["expected_behavior"],
                        "description": scenario["description"],
                        "prompt": scenario["prompt"][:150] + "...",
                        "response": response[:400] + "..." if len(response) > 400 else response,
                        "handled_gracefully": handled_gracefully,
                        "recovery_attempted": recovery_attempted,
                        "passed": handled_gracefully,
                        "conversation_id": conversation_id,
                    }
                )

                graceful_status = "✅ GRACEFUL" if handled_gracefully else "❌ UNGRACEFUL"
                recovery_status = "🔄 RECOVERED" if recovery_attempted else "⚠️ NO RECOVERY"
                print(f"  {graceful_status} {recovery_status}")

            except Exception as e:
                # Ironically, we need to handle errors in our error testing
                print(f"  💥 TESTING ERROR: {e}")
                results.append(
                    {
                        "name": scenario["name"],
                        "category": scenario.get("category", "unknown"),
                        "error_type": scenario.get("error_type", "unknown"),
                        "testing_error": str(e),  # Meta-error in error testing
                        "handled_gracefully": False,
                        "recovery_attempted": False,
                        "passed": False,
                    }
                )

        duration = time.time() - start_time
        pass_rate = passed_tests / len(selected_scenarios) if selected_scenarios else 0.0
        recovery_rate = (
            recovery_success_count / len(selected_scenarios) if selected_scenarios else 0.0
        )
        benchmark_passed = pass_rate >= 0.6 and recovery_rate >= 0.5  # 60% graceful + 50% recovery

        # Analyze error handling patterns
        category_analysis = self._analyze_by_error_category(results)
        recovery_analysis = self._analyze_recovery_strategies(results)

        return {
            "name": self.name,
            "benchmark_passed": benchmark_passed,
            "duration": duration,
            "summary": {
                "total_tests": len(results),
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "graceful_handling_rate": pass_rate,
                "recovery_attempts": recovery_success_count,
                "recovery_rate": recovery_rate,
                "error_category_breakdown": category_analysis,
                "recovery_strategy_analysis": recovery_analysis,
            },
            "results": results,
            "metadata": {
                "evaluation_type": "Error Recovery & Resilience",
                "production_readiness_indicator": True,
                "error_categories_tested": list(
                    {s.get("category", "unknown") for s in selected_scenarios}
                ),
                "recovery_strategies_tested": list(
                    {s.get("recovery_strategy", "unknown") for s in selected_scenarios}
                ),
                "sample_size": self.sample_size,
                "min_required_pass_rate": 0.6,
                "min_required_recovery_rate": 0.5,
                "showcase_capabilities": [
                    "Graceful error handling",
                    "Recovery strategy implementation",
                    "Workflow resilience under failure",
                    "Production-ready robustness",
                ],
            },
        }

    def _analyze_by_error_category(self, results: list[dict]) -> dict[str, Any]:
        """Analyze error handling success by error category."""
        categories = {}

        for result in results:
            category = result.get("category", "unknown")
            if category not in categories:
                categories[category] = {
                    "total": 0,
                    "handled_gracefully": 0,
                    "recovery_attempted": 0,
                }

            categories[category]["total"] += 1
            if result.get("handled_gracefully", False):
                categories[category]["handled_gracefully"] += 1
            if result.get("recovery_attempted", False):
                categories[category]["recovery_attempted"] += 1

        # Calculate success rates
        for category in categories:
            total = categories[category]["total"]
            if total > 0:
                categories[category]["graceful_rate"] = (
                    categories[category]["handled_gracefully"] / total
                )
                categories[category]["recovery_rate"] = (
                    categories[category]["recovery_attempted"] / total
                )
            else:
                categories[category]["graceful_rate"] = 0.0
                categories[category]["recovery_rate"] = 0.0

        return categories

    def _analyze_recovery_strategies(self, results: list[dict]) -> dict[str, Any]:
        """Analyze effectiveness of different recovery strategies."""
        strategies = {}

        for result in results:
            strategy = result.get("recovery_strategy", "unknown")
            if strategy not in strategies:
                strategies[strategy] = {"total": 0, "successful": 0}

            strategies[strategy]["total"] += 1
            if result.get("recovery_attempted", False):
                strategies[strategy]["successful"] += 1

        # Calculate effectiveness rates
        for strategy in strategies:
            total = strategies[strategy]["total"]
            strategies[strategy]["effectiveness"] = (
                strategies[strategy]["successful"] / total if total > 0 else 0.0
            )

        return strategies
