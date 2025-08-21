"""SWE-bench Lite evaluation with authentic dataset integration."""

import time
from typing import Any

from datasets import load_dataset

from ..eval_logging import EvalLogger
from ..judges.judge import Judge
from ..utils.sampling import BenchmarkSampler, validate_sample_quality


class SWEBenchmark:
    """SWE-bench Lite evaluation with authentic dataset integration."""

    name = "swe_benchmark"
    description = "SWE-bench Lite: Authentic software engineering benchmark"

    def __init__(self, sample_size: int = 50, random_seed: int = 42):
        """
        Initialize SWE-bench evaluation.

        Args:
            sample_size: Number of examples to sample (default 50 for manageable evaluation)
            random_seed: Random seed for reproducible sampling
        """
        self.judge = Judge()
        self.logger = EvalLogger()
        self.sample_size = sample_size
        self.sampler = BenchmarkSampler(random_seed=random_seed)
        self._dataset = None
        self._sample = None

    def _load_authentic_dataset(self) -> list[dict[str, Any]]:
        """Load authentic SWE-bench Lite dataset."""
        if self._dataset is None:
            print("📥 Loading SWE-bench Lite dataset...")
            dataset = load_dataset("princeton-nlp/SWE-bench_Lite")
            self._dataset = list(dataset["test"])
            print(f"✅ Loaded {len(self._dataset)} authentic SWE-bench examples")
        return self._dataset

    def _create_representative_sample(self) -> list[dict[str, Any]]:
        """Create representative sample from authentic dataset."""
        if self._sample is None:
            dataset = self._load_authentic_dataset()

            # Stratified sampling by repository for diversity
            self._sample = self.sampler.stratified_sample(
                dataset, self.sample_size, stratify_by="repo"
            )

            # Validate sample quality
            quality_metrics = validate_sample_quality(dataset, self._sample, stratify_field="repo")

            print("📊 Sample quality metrics:")
            print(f"  Sample size: {quality_metrics['sample_size']}")
            print(f"  Sample ratio: {quality_metrics['sample_ratio']:.2%}")
            if "distribution_error" in quality_metrics:
                print(f"  Distribution error: {quality_metrics['distribution_error']:.3f}")

        return self._sample

    async def execute(self) -> dict[str, Any]:
        """Execute SWE-bench evaluation with authentic dataset."""
        from cogency import Agent

        print("💻 Testing SWE-bench Lite...")
        start_time = time.time()

        # Load authentic representative sample
        test_cases = self._create_representative_sample()

        # Agent with full development toolset and configured provider
        from ..config import get_agent_provider

        provider = get_agent_provider()
        agent = Agent(
            "swe_tester", tools=["files", "shell", "search"], max_iterations=15, llm=provider
        )

        results = []
        total_tests = len(test_cases)
        passed_tests = 0
        confidence_scores = []

        for i, test_case in enumerate(test_cases):
            print(f"SWE ({i + 1}/{total_tests}): {test_case['repo']} - {test_case['instance_id']}")

            try:
                response, conversation_id = await agent.run(test_case["problem_statement"])

                # Judge the quality of software engineering solution
                judge_result = await self._evaluate_swe_response(test_case, response)

                # Track confidence for human review triggers
                confidence_scores.append(judge_result.score.confidence)

                # Log result with authentic metadata
                self.logger.log_result(
                    eval_name=f"swe_{test_case['repo'].replace('/', '_')}_{test_case['instance_id']}",
                    judge_result=judge_result,
                    agent_metadata={
                        "repo": test_case["repo"],
                        "instance_id": test_case["instance_id"],
                        "created_at": test_case.get("created_at"),
                        "base_commit": test_case.get("base_commit"),
                    },
                    execution_time=0.0,
                )

                test_passed = judge_result.score.value >= 5.0
                if test_passed:
                    passed_tests += 1

                results.append(
                    {
                        "repo": test_case["repo"],
                        "instance_id": test_case["instance_id"],
                        "problem": test_case["problem_statement"][:150] + "...",
                        "response": response[:300] + "..." if len(response) > 300 else response,
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
                        "repo": test_case["repo"],
                        "instance_id": test_case["instance_id"],
                        "problem": test_case["problem_statement"],
                        "error": str(e),
                        "passed": False,
                        "needs_human_review": True,
                    }
                )

        duration = time.time() - start_time
        pass_rate = passed_tests / total_tests if total_tests > 0 else 0.0
        benchmark_passed = pass_rate >= 0.3  # 30% threshold for SWE-bench (realistic)

        # Statistical validation metrics
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0
        )
        low_confidence_count = sum(1 for c in confidence_scores if c < 0.7)
        human_review_needed = [r for r in results if r.get("needs_human_review", False)]

        # Repository distribution analysis
        repo_stats = self._analyze_by_repository(results)

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
                "repository_breakdown": repo_stats,
            },
            "results": results,
            "metadata": {
                "benchmark_type": "SWE-bench Lite (Authentic)",
                "dataset_source": "princeton-nlp/SWE-bench_Lite",
                "sample_size": self.sample_size,
                "sampling_method": "stratified_by_repository",
                "min_required_score": 5.0,
                "realistic_pass_threshold": 0.3,
                "confidence_threshold": 0.7,
                "authentic_dataset": True,
                "logging_report": self.logger.generate_report(),
            },
            "human_review_queue": human_review_needed,
        }

    def _analyze_by_repository(self, results: list) -> dict:
        """Analyze results by repository for authentic dataset insights."""
        repo_stats = {}

        for result in results:
            if "repo" in result:
                repo = result["repo"]
                if repo not in repo_stats:
                    repo_stats[repo] = {"total": 0, "passed": 0}

                repo_stats[repo]["total"] += 1
                if result.get("passed", False):
                    repo_stats[repo]["passed"] += 1

        # Calculate pass rates
        for repo in repo_stats:
            if repo_stats[repo]["total"] > 0:
                repo_stats[repo]["pass_rate"] = (
                    repo_stats[repo]["passed"] / repo_stats[repo]["total"]
                )
            else:
                repo_stats[repo]["pass_rate"] = 0.0

        return repo_stats
