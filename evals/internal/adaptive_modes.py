"""Adaptive mode switching evaluation - migrated from archive."""

import time
from typing import Any

from ..judges.claude_judge import ClaudeJudge
from ..logging import EvalLogger


class AdaptiveModeSwitching:
    """Test agent's ability to adaptively switch between fast/deep reasoning modes."""

    name = "adaptive_mode_switching"
    description = "Adaptive fast/deep mode switching based on query complexity"

    def __init__(self):
        self.judge = ClaudeJudge()
        self.logger = EvalLogger()

    async def execute(self) -> dict[str, Any]:
        """Execute adaptive mode switching evaluation."""
        from cogency import Agent

        print("🧠 Testing Adaptive Mode Switching...")
        start_time = time.time()

        agent = Agent("mode_tester", max_iterations=15, observe=True)

        # Test cases designed to trigger different reasoning modes
        test_cases = [
            # Simple queries (should use fast mode - minimal iterations)
            ("What's 2+2?", "fast", "Simple arithmetic should require minimal reasoning"),
            ("Say hello", "fast", "Basic greeting should be fast response"),
            ("What color is grass?", "fast", "Basic factual knowledge should be quick"),
            # Complex queries (should use deep mode - more iterations)
            (
                "Analyze the philosophical implications of consciousness in AI systems",
                "deep",
                "Complex philosophical analysis requires deep reasoning",
            ),
            (
                "Design a distributed system architecture for handling 1M users",
                "deep",
                "System architecture design requires extensive planning",
            ),
            (
                "Debug this complex race condition in concurrent programming",
                "deep",
                "Complex debugging requires systematic analysis",
            ),
            # Adaptive queries (mode should match complexity)
            (
                "Explain quantum computing fundamentals",
                "adaptive",
                "Educational explanation can be fast or deep",
            ),
            (
                "How do neural networks work?",
                "adaptive",
                "Technical explanation allows adaptive depth",
            ),
        ]

        all_results = []
        passed_count = 0
        total_tests = len(test_cases)

        for query, expected_mode, description in test_cases:
            # Clear agent logs for clean measurement
            agent._logs = []

            result = await agent.run_async(query)

            # Analyze reasoning depth through log analysis
            logs = agent.logs(mode="debug") if hasattr(agent, "logs") else []

            # Count reasoning steps and tool calls
            reasoning_steps = len([log for log in logs if log.get("type") == "reason"])
            tool_calls = len([log for log in logs if log.get("type") == "tool"])
            total_operations = reasoning_steps + tool_calls

            # Determine actual mode based on operational complexity
            if total_operations <= 3:
                actual_mode = "fast"
            elif total_operations >= 6:
                actual_mode = "deep"
            else:
                actual_mode = "moderate"

            # Validate mode appropriateness
            mode_appropriate = False
            if expected_mode == "fast":
                mode_appropriate = actual_mode == "fast"
            elif expected_mode == "deep":
                mode_appropriate = actual_mode in ["deep", "moderate"]  # Allow some flexibility
            elif expected_mode == "adaptive":
                mode_appropriate = True  # Adaptive is always appropriate if system responds

            if mode_appropriate:
                passed_count += 1

            # Response quality indicators
            response_length = len(result)
            response_quality = "detailed" if response_length > 200 else "concise"

            test_result = {
                "query": query,
                "expected_mode": expected_mode,
                "actual_mode": actual_mode,
                "reasoning_steps": reasoning_steps,
                "tool_calls": tool_calls,
                "total_operations": total_operations,
                "mode_appropriate": mode_appropriate,
                "response_length": response_length,
                "response_quality": response_quality,
                "description": description,
            }

            all_results.append(test_result)

        # Calculate performance metrics
        mode_accuracy = passed_count / total_tests
        fast_mode_tests = [r for r in all_results if r["expected_mode"] == "fast"]
        deep_mode_tests = [r for r in all_results if r["expected_mode"] == "deep"]
        adaptive_tests = [r for r in all_results if r["expected_mode"] == "adaptive"]

        fast_accuracy = (
            sum(1 for t in fast_mode_tests if t["mode_appropriate"]) / len(fast_mode_tests)
            if fast_mode_tests
            else 1.0
        )
        deep_accuracy = (
            sum(1 for t in deep_mode_tests if t["mode_appropriate"]) / len(deep_mode_tests)
            if deep_mode_tests
            else 1.0
        )
        adaptive_accuracy = (
            sum(1 for t in adaptive_tests if t["mode_appropriate"]) / len(adaptive_tests)
            if adaptive_tests
            else 1.0
        )

        # Judge the adaptive mode switching quality
        combined_performance = f"""Mode Switching Performance:
Fast Mode Accuracy: {fast_accuracy:.2f}
Deep Mode Accuracy: {deep_accuracy:.2f}
Adaptive Mode Accuracy: {adaptive_accuracy:.2f}
Overall Accuracy: {mode_accuracy:.2f}

Sample Results:
{chr(10).join([f"- {r['query'][:50]}... → {r['actual_mode']} ({r['total_operations']} ops)" for r in all_results[:3]])}"""

        judge_result = await self._evaluate_mode_switching_quality(
            combined_performance, all_results, mode_accuracy
        )

        # Log result
        self.logger.log_result(
            eval_name="adaptive_mode_switching",
            judge_result=judge_result,
            agent_metadata={
                "total_tests": total_tests,
                "passed_tests": passed_count,
                "fast_accuracy": fast_accuracy,
                "deep_accuracy": deep_accuracy,
            },
            execution_time=time.time() - start_time,
        )

        test_passed = mode_accuracy >= 0.7 and judge_result.score.value >= 6.0

        duration = time.time() - start_time

        return {
            "name": self.name,
            "benchmark_passed": test_passed,
            "duration": duration,
            "summary": {
                "mode_accuracy": mode_accuracy,
                "fast_accuracy": fast_accuracy,
                "deep_accuracy": deep_accuracy,
                "adaptive_accuracy": adaptive_accuracy,
                "judge_score": judge_result.score.value,
            },
            "results": [
                {
                    "scenario": "adaptive mode switching",
                    "total_tests": total_tests,
                    "passed_tests": passed_count,
                    "mode_accuracy": mode_accuracy,
                    "judge_score": judge_result.score.value,
                    "judge_reasoning": judge_result.score.reasoning,
                    "passed": test_passed,
                    "detailed_results": all_results,
                }
            ],
            "metadata": {
                "evaluation_focus": "adaptive_reasoning",
                "pattern_source": "archive/mode_switching.py",
                "fast_mode_tests": len(fast_mode_tests),
                "deep_mode_tests": len(deep_mode_tests),
                "adaptive_tests": len(adaptive_tests),
                "logging_report": self.logger.generate_report(),
            },
        }

    async def _evaluate_mode_switching_quality(
        self, performance_summary: str, results: list, accuracy: float
    ):
        """Evaluate adaptive mode switching quality."""

        criteria = f"""Adaptive Mode Switching Assessment:

Performance Summary:
{performance_summary}

Rate the agent's adaptive mode switching capabilities:

1. **Fast Mode Efficiency**: Does it handle simple queries with minimal reasoning steps?
2. **Deep Mode Engagement**: Does it use thorough reasoning for complex queries?
3. **Adaptive Intelligence**: Does it match reasoning depth to query complexity?
4. **Resource Optimization**: Does it avoid over-processing simple queries?
5. **Quality Maintenance**: Does it maintain response quality across modes?

Score 1-3: Poor mode selection, inefficient reasoning allocation
Score 4-6: Partial adaptivity with some appropriate mode selection
Score 7-8: Good adaptive behavior with efficient mode switching
Score 9-10: Excellent intelligence in matching reasoning depth to complexity"""

        return await self.judge.evaluate(
            agent_response=performance_summary,
            test_case="Adaptive mode switching across query complexities",
            criteria=criteria,
            context={
                "evaluation_focus": "adaptive_reasoning",
                "accuracy": accuracy,
                "test_count": len(results),
                "mode_types": ["fast", "deep", "adaptive"],
            },
        )
