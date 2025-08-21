"""GAIA benchmark evaluation with authentic dataset integration.

Uses the official GAIA dataset from Hugging Face with proper access patterns.
GAIA tests general AI assistants on realistic multi-step tasks requiring
tool usage, web browsing, and reasoning across multiple domains.
"""

import time
from typing import Any

from datasets import load_dataset

from ..eval_logging import EvalLogger
from ..judges.judge import Judge
from ..utils.sampling import BenchmarkSampler, validate_sample_quality


class GAIABenchmark:
    """GAIA benchmark evaluation with authentic dataset integration."""

    name = "gaia_benchmark"
    description = "GAIA: Authentic general AI assistants benchmark"

    def __init__(self, sample_size: int = 30, random_seed: int = 42):
        """
        Initialize GAIA evaluation.

        Args:
            sample_size: Number of examples to sample (default 30 for manageable evaluation)
            random_seed: Random seed for reproducible sampling
        """
        self.judge = Judge()
        self.logger = EvalLogger()
        self.sample_size = sample_size
        self.sampler = BenchmarkSampler(random_seed=random_seed)
        self._dataset = None
        self._sample = None

    def _load_authentic_dataset(self) -> list[dict[str, Any]]:
        """Load authentic GAIA dataset."""
        if self._dataset is None:
            print("📥 Loading GAIA dataset...")
            try:
                # Load official GAIA dataset from Hugging Face
                dataset = load_dataset("gaia-benchmark/GAIA")
                # Use validation set for evaluation (test set requires submission)
                self._dataset = list(dataset["validation"])
                print(f"✅ Loaded {len(self._dataset)} authentic GAIA examples")
            except Exception as e:
                print(f"⚠️  Could not load GAIA dataset: {e}")
                print("   This may require HF authentication or dataset access approval")
                print("   See: https://huggingface.co/datasets/gaia-benchmark/GAIA")
                # Fallback to empty list rather than synthetic data
                self._dataset = []
        return self._dataset

    def _create_representative_sample(self) -> list[dict[str, Any]]:
        """Create representative sample from authentic dataset."""
        if self._sample is None:
            dataset = self._load_authentic_dataset()

            if not dataset:
                print("⚠️  No GAIA dataset available - skipping evaluation")
                return []

            # Stratified sampling by Level for balanced evaluation
            self._sample = self.sampler.stratified_sample(
                dataset, self.sample_size, stratify_by="Level"
            )

            # Validate sample quality
            quality_metrics = validate_sample_quality(dataset, self._sample, stratify_field="Level")

            print("📊 GAIA sample quality metrics:")
            print(f"  Sample size: {quality_metrics['sample_size']}")
            print(f"  Sample ratio: {quality_metrics['sample_ratio']:.2%}")
            if "distribution_error" in quality_metrics:
                print(f"  Level distribution error: {quality_metrics['distribution_error']:.3f}")

        return self._sample

    async def execute(self) -> dict[str, Any]:
        """Execute GAIA benchmark evaluation."""
        from cogency import Agent

        print("🧠 Testing GAIA Multi-step Reasoning...")
        start_time = time.time()

        # Load authentic representative sample
        test_cases = self._create_representative_sample()

        if not test_cases:
            return {
                "name": self.name,
                "benchmark_passed": False,
                "error": "No GAIA dataset available - requires Hugging Face authentication",
                "summary": {"total_tests": 0, "passed_tests": 0, "pass_rate": 0.0},
            }

        # Agent with reasoning and search capabilities
        from ..config import get_agent_provider

        provider = get_agent_provider()
        agent = Agent("gaia_tester", tools=["search", "files"], max_iterations=12, llm=provider)

        results = []
        total_tests = len(test_cases)
        passed_tests = 0
        confidence_scores = []

        for i, test_case in enumerate(test_cases):
            print(
                f"GAIA Level {test_case.get('Level', '?')} ({i + 1}/{total_tests}): {test_case.get('task', 'Unknown task')[:50]}..."
            )

            try:
                # Use the Question field from authentic GAIA data
                question = test_case.get("Question", test_case.get("task", "No question found"))
                response, conversation_id = await agent.run(question)

                # Judge the quality of multi-step reasoning
                judge_result = await self._evaluate_gaia_response(test_case, response)

                # Track confidence for human review triggers
                confidence_scores.append(judge_result.score.confidence)

                # Log result with authentic metadata
                self.logger.log_result(
                    eval_name=f"gaia_level_{test_case.get('Level', 'unknown')}_{i + 1}",
                    judge_result=judge_result,
                    agent_metadata={
                        "level": test_case.get("Level"),
                        "task": test_case.get("task", question[:100]),
                        "final_answer": test_case.get("Final answer"),
                        "annotator_metadata": test_case.get("Annotator Metadata", {}),
                    },
                    execution_time=0.0,
                )

                test_passed = judge_result.score.value >= 6.0
                if test_passed:
                    passed_tests += 1

                results.append(
                    {
                        "level": test_case.get("Level"),
                        "task": question[:100] + "..." if len(question) > 100 else question,
                        "final_answer": test_case.get("Final answer"),
                        "response": response[:200] + "..." if len(response) > 200 else response,
                        "score": judge_result.score.value,
                        "confidence": judge_result.score.confidence,
                        "reasoning": judge_result.score.reasoning,
                        "passed": test_passed,
                        "needs_human_review": judge_result.score.confidence < 0.7,
                    }
                )

                status = "✅ PASSED" if test_passed else "❌ FAILED"
                confidence_flag = "🔍" if judge_result.score.confidence < 0.7 else ""
                print(
                    f"  {status} {confidence_flag} - Score: {judge_result.score.value}/10 (conf: {judge_result.score.confidence:.2f})"
                )

            except Exception as e:
                print(f"  💥 ERROR: {e}")
                results.append(
                    {
                        "level": test_case.get("Level"),
                        "task": test_case.get("Question", "Unknown"),
                        "error": str(e),
                        "passed": False,
                        "needs_human_review": True,
                    }
                )

        duration = time.time() - start_time
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        benchmark_passed = pass_rate >= 0.6  # 60% threshold for GAIA

        # Statistical validation metrics
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        )
        low_confidence_count = sum(1 for c in confidence_scores if c < 0.7)
        human_review_needed = [r for r in results if r.get("needs_human_review", False)]

        return {
            "name": self.name,
            "benchmark_passed": benchmark_passed,
            "duration": duration,
            "summary": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "pass_rate": pass_rate,
                "avg_confidence": avg_confidence,
                "low_confidence_count": low_confidence_count,
                "human_review_needed": len(human_review_needed),
                "level_breakdown": self._analyze_by_level(results),
            },
            "results": results,
            "metadata": {
                "benchmark_type": "GAIA Authentic Dataset",
                "dataset_source": "gaia-benchmark/GAIA",
                "sample_size": self.sample_size,
                "sampling_method": "stratified_by_difficulty_level",
                "difficulty_levels": [1, 2, 3],
                "min_required_score": 6.0,
                "confidence_threshold": 0.7,
                "authentic_dataset": True,
                "logging_report": self.logger.generate_report(),
            },
            "human_review_queue": human_review_needed,
        }

    async def _evaluate_gaia_response(self, test_case: dict, response: str):
        """Evaluate GAIA response quality against authentic dataset."""

        question = test_case.get("Question", test_case.get("task", "Unknown question"))
        expected_answer = test_case.get("Final answer", "No expected answer provided")

        criteria = f"""GAIA Authentic Benchmark Assessment - Level {test_case.get("Level", "?")}:

Question: {question}
Expected Answer: {expected_answer}

Rate the agent's multi-step reasoning and task completion:

1. **Task Understanding**: Did it understand what was being asked?
2. **Information Gathering**: Did it collect relevant, accurate information using appropriate tools?
3. **Reasoning Process**: Was the logical process sound and well-structured?
4. **Answer Quality**: How close is the response to the expected answer?
5. **Tool Usage**: Did it effectively use search and other required tools?

GAIA Level {test_case.get("Level", "?")} Expectations:
- Level 1: Direct fact-finding with tool usage and verification
- Level 2: Multi-step research with logical connections and synthesis
- Level 3: Complex analysis requiring deep reasoning across multiple domains

This uses the authentic GAIA dataset with real questions and verified answers.

Score 1-3: Incorrect approach or fundamentally flawed reasoning
Score 4-6: Partial success with some reasoning gaps or accuracy issues
Score 7-8: Good reasoning with accurate approach, minor inaccuracies
Score 9-10: Excellent reasoning with correct answer and clear methodology"""

        return await self.judge.evaluate(
            agent_response=response,
            test_case=question,
            criteria=criteria,
            context={
                "benchmark": "GAIA Authentic",
                "difficulty_level": test_case.get("Level"),
                "expected_answer": expected_answer,
                "annotator_metadata": test_case.get("Annotator Metadata", {}),
                "authentic_dataset": True,
            },
        )

    def _analyze_by_level(self, results: list) -> dict:
        """Analyze results by difficulty level."""
        level_stats = {
            1: {"total": 0, "passed": 0},
            2: {"total": 0, "passed": 0},
            3: {"total": 0, "passed": 0},
        }

        for result in results:
            if "level" in result and result["level"] in level_stats:
                level = result["level"]
                level_stats[level]["total"] += 1
                if result.get("passed", False):
                    level_stats[level]["passed"] += 1

        # Calculate pass rates
        for level in level_stats:
            total = level_stats[level]["total"]
            if total > 0:
                level_stats[level]["pass_rate"] = level_stats[level]["passed"] / total
            else:
                level_stats[level]["pass_rate"] = 0.0

        return level_stats
