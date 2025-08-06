"""Adaptive mode switching evaluation."""

from ..eval import Eval


class ModeSwitching(Eval):
    """Test agent's ability to adaptively switch between fast/deep reasoning modes."""

    name = "mode_switching"
    description = "Test adaptive fast/deep mode switching based on query complexity"

    async def run(self):
        # Test cases designed to trigger different reasoning modes
        test_cases = [
            # Simple queries (should use fast mode)
            ("What's 2+2?", "fast"),
            ("Say hello", "fast"),
            ("What time is it?", "fast"),
            # Complex queries (should use deep mode)
            ("Analyze the philosophical implications of consciousness in AI systems", "deep"),
            ("Design a distributed system architecture for handling 1M users", "deep"),
            ("Debug this complex race condition in concurrent code", "deep"),
            # Ambiguous queries (mode switching should be adaptive)
            ("Help me understand quantum computing", "adaptive"),
            ("Explain how neural networks work", "adaptive"),
        ]

        agent = self.agent("mode_tester", max_iterations=15)
        all_traces = []
        passed_count = 0

        for query, expected_mode in test_cases:
            result = await agent.run_async(query)

            # Get execution state to check iterations used
            iterations = 0
            reasoning_depth = "unknown"
            try:
                runtime = await agent._get_executor()
                if runtime and runtime.executor and runtime.executor.last_state:
                    iterations = runtime.executor.last_state.execution.iteration
                    # Fast mode: 0-2 iterations, Deep mode: 3+ iterations
                    reasoning_depth = "fast" if iterations <= 2 else "deep"
            except Exception:
                reasoning_depth = "unknown"

            # Validate mode selection
            correct_mode = False
            if expected_mode == "fast":
                correct_mode = reasoning_depth == "fast"
            elif expected_mode == "deep":
                correct_mode = reasoning_depth == "deep"
            elif expected_mode == "adaptive":
                # Adaptive is correct if it chose either mode appropriately
                correct_mode = reasoning_depth in ["fast", "deep"]

            if correct_mode:
                passed_count += 1

            all_traces.append(
                {
                    "query": query,
                    "expected_mode": expected_mode,
                    "actual_iterations": iterations,
                    "reasoning_depth": reasoning_depth,
                    "correct_mode": correct_mode,
                    "response_length": len(result),
                }
            )

        score = passed_count / len(test_cases)
        passed = score >= 0.7  # 70% threshold for adaptive behavior

        return {
            "name": self.name,
            "passed": passed,
            "score": score,
            "duration": 0.0,
            "traces": all_traces,
            "metadata": {
                "test_cases": len(test_cases),
                "passed": passed_count,
                "fast_mode_accuracy": sum(
                    1 for t in all_traces if t["expected_mode"] == "fast" and t["correct_mode"]
                ),
                "deep_mode_accuracy": sum(
                    1 for t in all_traces if t["expected_mode"] == "deep" and t["correct_mode"]
                ),
            },
        }
