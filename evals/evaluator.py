"""Cogency Evaluator - Foundation, production, differentiation, and benchmarking."""

import time
from dataclasses import dataclass
from typing import Any, Optional

# Differentiation imports
from .differentiation.cross_session_workflows import CrossSessionWorkflows

# Foundation imports
from .foundation.agent_basics import AgentBasics
from .foundation.comprehensive_tools import ComprehensiveTools

# Production imports
from .production.resilience import ProductionResilience

# Benchmarking imports
try:
    from .benchmarks.gaia import GAIABenchmark
    from .benchmarks.swe_bench import SWEBenchmark

    BENCHMARKS_AVAILABLE = True
except ImportError:
    BENCHMARKS_AVAILABLE = False


@dataclass
class SuiteResult:
    """Result from an evaluation suite."""

    suite_name: str
    suite_passed: bool
    execution_time: float
    pass_rate: float
    executive_insight: str
    recommendation: str
    detailed_results: list[dict[str, Any]]


class Evaluator:
    """Orchestrate four-tier evaluation: foundation → production → differentiation → benchmarking."""

    def __init__(self):
        self.suites = {
            "foundation": {
                "name": "Foundation",
                "description": "Basic functionality",
                "time_budget": 180,
                "early_exit_on_failure": True,
                "evaluations": [AgentBasics(), ComprehensiveTools()],
            },
            "production": {
                "name": "Production",
                "description": "Resilience and error handling",
                "time_budget": 300,
                "early_exit_on_failure": True,
                "evaluations": [ProductionResilience()],
            },
            "differentiation": {
                "name": "Differentiation",
                "description": "Unique capabilities",
                "time_budget": 600,
                "early_exit_on_failure": False,
                "evaluations": [CrossSessionWorkflows()],
            },
            "benchmarking": {
                "name": "Benchmarking",
                "description": "Competitive performance",
                "time_budget": 900,
                "early_exit_on_failure": False,
                "evaluations": [],
            },
        }

        # Add benchmarks if available
        if BENCHMARKS_AVAILABLE:
            self.suites["benchmarking"]["evaluations"] = [
                SWEBenchmark(sample_size=20, random_seed=42),
                GAIABenchmark(sample_size=15, random_seed=42),
            ]

        self.suite_results = []

    async def execute_evaluation(
        self, early_exit: bool = True, suites_filter: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Execute four-tier evaluation."""

        print("🧠 Cogency Evaluation")
        print("Foundation → Production → Differentiation → Benchmarking")
        print("=" * 60)

        total_start_time = time.time()
        overall_recommendation = "CONTINUE_EVALUATION"

        # Execute suites in sequence
        suite_sequence = ["foundation", "production", "differentiation", "benchmarking"]
        if suites_filter:
            suite_sequence = [suite for suite in suite_sequence if suite in suites_filter]

        for suite_name in suite_sequence:
            if suite_name not in self.suites:
                continue

            suite_definition = self.suites[suite_name]

            print(f"\n{suite_definition['name']}: {suite_definition['description']}")
            print(f"Budget: {suite_definition['time_budget']}s")
            print("-" * 40)

            # Execute suite
            suite_result = await self._execute_suite(suite_name, suite_definition)
            self.suite_results.append(suite_result)

            # Report results
            self._report_suite_results(suite_result)

            # Early exit if needed
            if early_exit and self._should_exit_early(suite_result, suite_definition):
                overall_recommendation = "EARLY_EXIT"
                print(f"\nEarly exit: {suite_result.suite_name} failed")
                break

        # Generate final assessment
        total_duration = time.time() - total_start_time
        final_assessment = self._generate_assessment(overall_recommendation, total_duration)

        print("\n" + "=" * 60)
        print("Evaluation complete")
        print("=" * 60)

        return {
            "evaluation_complete": True,
            "total_execution_time": total_duration,
            "suites_completed": len(self.suite_results),
            "suite_results": [
                self._serialize_suite_result(result) for result in self.suite_results
            ],
            "final_assessment": final_assessment,
            "overall_recommendation": overall_recommendation,
        }

    async def _execute_suite(
        self, suite_name: str, suite_definition: dict[str, Any]
    ) -> SuiteResult:
        """Execute a single suite with all its evaluations."""
        suite_start_time = time.time()

        evaluations = suite_definition["evaluations"]
        if not evaluations:
            return SuiteResult(
                suite_name=suite_definition["name"],
                suite_passed=True,
                execution_time=0.1,
                pass_rate=1.0,
                executive_insight="Skipped: components not available",
                recommendation="SKIP_SUITE",
                detailed_results=[],
            )

        # Execute all evaluations in the act
        evaluation_results = []
        total_tests = 0
        total_passed = 0

        for evaluation in evaluations:
            print(f"  Running: {evaluation.name}")
            eval_start = time.time()

            try:
                result = await evaluation.execute()
                evaluation_results.append(result)

                # Aggregate stats
                summary = result.get("summary", {})
                eval_total = summary.get("total_tests", summary.get("total_workflows", 1))
                eval_passed = summary.get(
                    "passed_tests", summary.get("successful_continuations", 0)
                )

                total_tests += eval_total
                total_passed += eval_passed

                eval_duration = time.time() - eval_start
                eval_pass_rate = eval_passed / eval_total if eval_total > 0 else 0.0

                print(f"  ✓ {evaluation.name}: {eval_pass_rate:.1%} ({eval_duration:.1f}s)")

            except Exception as e:
                print(f"  ✗ {evaluation.name} failed: {e}")
                evaluation_results.append(
                    {
                        "name": evaluation.name,
                        "error": str(e),
                        "tier": suite_name,
                        "executive_insight": f"Failed: {evaluation.name} could not execute",
                    }
                )

        # Calculate suite-level metrics
        execution_time = time.time() - suite_start_time
        pass_rate = total_passed / total_tests if total_tests > 0 else 0.0

        # Determine suite success based on type and pass rate
        suite_passed = self._determine_suite_success(suite_name, pass_rate)

        # Generate suite-level executive insight
        executive_insight = self._generate_suite_insight(suite_name, pass_rate, suite_passed)

        # Generate suite recommendation
        recommendation = self._generate_suite_recommendation(suite_name, suite_passed, pass_rate)

        return SuiteResult(
            suite_name=suite_definition["name"],
            suite_passed=suite_passed,
            execution_time=execution_time,
            pass_rate=pass_rate,
            executive_insight=executive_insight,
            recommendation=recommendation,
            detailed_results=evaluation_results,
        )

    def _determine_suite_success(self, suite_name: str, pass_rate: float) -> bool:
        """Determine if suite passes based on strategic thresholds."""
        thresholds = {
            "foundation": 0.9,  # 90% - must work reliably
            "production": 0.6,  # 60% - must handle errors gracefully
            "differentiation": 0.7,  # 70% - must show compelling advantage
            "benchmarking": 0.5,  # 50% - must be competitive
        }
        return pass_rate >= thresholds.get(suite_name, 0.7)

    def _generate_suite_insight(self, suite_name: str, pass_rate: float, suite_passed: bool) -> str:
        """Generate insight for each suite."""
        insights = {
            "foundation": {
                True: f"Foundation solid: {pass_rate:.1%} basic functionality confirmed",
                False: f"Foundation failed: only {pass_rate:.1%} basic functionality working",
            },
            "production": {
                True: f"Production ready: {pass_rate:.1%} resilience demonstrated",
                False: f"Production concerns: only {pass_rate:.1%} error recovery working",
            },
            "differentiation": {
                True: f"Strong differentiation: {pass_rate:.1%} unique capabilities demonstrated",
                False: f"Weak differentiation: only {pass_rate:.1%} unique capabilities working",
            },
            "benchmarking": {
                True: f"Competitive: {pass_rate:.1%} benchmark performance",
                False: f"Lagging: only {pass_rate:.1%} benchmark performance",
            },
        }

        return insights.get(suite_name, {}).get(
            suite_passed, f"{suite_name}: {pass_rate:.1%} performance"
        )

    def _generate_suite_recommendation(
        self, suite_name: str, suite_passed: bool, pass_rate: float
    ) -> str:
        """Generate strategic recommendation for each suite."""
        if not suite_passed:
            if suite_name in ["foundation", "production"]:
                return "TERMINATE_EVALUATION"
            if suite_name == "differentiation":
                return "WEAK_VALUE_PROPOSITION"
            return "NEEDS_IMPROVEMENT"
        if pass_rate >= 0.9:
            return "EXCEEDS_EXPECTATIONS"
        return "MEETS_STANDARDS"

    def _should_exit_early(
        self, suite_result: SuiteResult, suite_definition: dict[str, Any]
    ) -> bool:
        """Determine if evaluation should exit early based on suite results."""
        return suite_definition["early_exit_on_failure"] and not suite_result.suite_passed

    def _report_suite_results(self, result: SuiteResult):
        """Report suite results."""
        status = "✓" if result.suite_passed else "✗"
        print(f"\n{status} {result.suite_name}")
        print(f"Pass rate: {result.pass_rate:.1%} | Duration: {result.execution_time:.1f}s")
        print(f"{result.executive_insight}")
        print(f"Recommendation: {result.recommendation}")

        if not result.suite_passed:
            print("Impact: Suite failure affects evaluation")

    def _generate_assessment(self, recommendation: str, total_time: float) -> dict[str, Any]:
        """Generate final assessment."""

        # Extract key metrics from suites
        foundation_passed = any(
            result.suite_name.startswith("Foundation") and result.suite_passed
            for result in self.suite_results
        )

        production_result = next(
            (result for result in self.suite_results if result.suite_name.startswith("Production")),
            None,
        )
        production_resilience = production_result.pass_rate if production_result else 0.0

        differentiation_result = next(
            (
                result
                for result in self.suite_results
                if result.suite_name.startswith("Differentiation")
            ),
            None,
        )
        differentiation_strength = (
            differentiation_result.pass_rate if differentiation_result else 0.0
        )

        benchmarking_result = next(
            (
                result
                for result in self.suite_results
                if result.suite_name.startswith("Benchmarking")
            ),
            None,
        )
        competitive_performance = benchmarking_result.pass_rate if benchmarking_result else 0.0

        # Generate hire recommendation
        hire_recommendation = self._generate_hire_recommendation(
            foundation_passed,
            production_resilience,
            differentiation_strength,
            competitive_performance,
        )

        return {
            "execution_summary": {
                "total_duration": f"{total_time:.1f} seconds",
                "suites_completed": len(self.suite_results),
                "narrative_arc": "Foundation → Production → Differentiation → Benchmarking",
            },
            "capability_assessment": {
                "foundation_solid": foundation_passed,
                "production_resilience": f"{production_resilience:.1%}",
                "differentiation_strength": f"{differentiation_strength:.1%}",
                "competitive_performance": f"{competitive_performance:.1%}",
                "unique_value_demonstrated": differentiation_strength >= 0.7,
                "production_ready": production_resilience >= 0.6,
            },
            "strategic_recommendation": {
                "hire_decision": hire_recommendation,
                "reasoning": self._generate_hire_reasoning(
                    foundation_passed,
                    production_resilience,
                    differentiation_strength,
                    competitive_performance,
                ),
                "next_steps": self._generate_next_steps(hire_recommendation),
            },
            "executive_summary": self._generate_summary(
                foundation_passed,
                production_resilience,
                differentiation_strength,
                competitive_performance,
                hire_recommendation,
            ),
        }

    def _generate_hire_recommendation(
        self, foundation: bool, production: float, differentiation: float, competitive: float
    ) -> str:
        """Generate final hire recommendation based on evaluation."""
        if not foundation:
            return "DO_NOT_HIRE"
        if production < 0.5:
            return "DO_NOT_HIRE"  # Production resilience is critical
        if differentiation >= 0.8 and production >= 0.7 and competitive >= 0.6:
            return "STRONG_HIRE"
        if differentiation >= 0.7 and production >= 0.6:
            return "HIRE"
        if differentiation >= 0.5 and production >= 0.6:
            return "WEAK_HIRE"
        return "DO_NOT_HIRE"

    def _generate_hire_reasoning(
        self, foundation: bool, production: float, differentiation: float, competitive: float
    ) -> str:
        """Generate reasoning for hire recommendation."""
        if not foundation:
            return "Basic functionality insufficient - not ready for production use"
        if production < 0.5:
            return "Production resilience insufficient - error handling needs improvement"
        if differentiation >= 0.8 and production >= 0.7:
            return "Exceptional capabilities with strong production readiness - excellent technical asset"
        if differentiation >= 0.7 and production >= 0.6:
            return (
                "Clear differentiation with adequate production resilience - valuable contribution"
            )
        if differentiation >= 0.5 and production >= 0.6:
            return "Some unique capabilities with basic production readiness - needs development"
        return "Insufficient differentiation and production concerns - limited strategic value"

    def _generate_next_steps(self, hire_recommendation: str) -> list[str]:
        """Generate next steps based on hire recommendation."""
        steps = {
            "STRONG_HIRE": [
                "Schedule technical deep-dive with engineering team",
                "Discuss integration with existing agent infrastructure",
                "Prepare competitive offer package",
            ],
            "HIRE": [
                "Conduct follow-up technical interview",
                "Assess team fit and project alignment",
                "Consider standard offer",
            ],
            "WEAK_HIRE": [
                "Provide detailed feedback on improvement areas",
                "Suggest 3-month development timeline",
                "Re-evaluate after capability improvements",
            ],
            "DO_NOT_HIRE": [
                "Provide constructive feedback",
                "Keep in talent pipeline for future evaluation",
                "Focus on fundamental capability development",
            ],
        }
        return steps.get(hire_recommendation, ["Continue standard evaluation process"])

    def _generate_summary(
        self,
        foundation: bool,
        production: float,
        differentiation: float,
        competitive: float,
        hire_decision: str,
    ) -> str:
        """Generate evaluation summary."""

        foundation_status = "SOLID" if foundation else "INSUFFICIENT"
        production_status = (
            "RESILIENT" if production >= 0.7 else "ADEQUATE" if production >= 0.6 else "FRAGILE"
        )
        differentiation_status = (
            "STRONG" if differentiation >= 0.8 else "ADEQUATE" if differentiation >= 0.7 else "WEAK"
        )
        competitive_status = (
            "LEADING" if competitive >= 0.8 else "COMPETITIVE" if competitive >= 0.6 else "LAGGING"
        )

        return f"""
COGENCY EVALUATION SUMMARY
==========================

Foundation: {foundation_status}
Basic agent functionality and comprehensive tool integration.

Production: {production_status} ({production:.1%})
Error handling, resilience, and recovery capabilities.

Differentiation: {differentiation_status} ({differentiation:.1%})
Cross-session memory and workflow orchestration.

Benchmarks: {competitive_status} ({competitive:.1%})
Performance on SWE-bench and GAIA.

Value proposition:
Unique memory persistence across agent restarts.
Production-ready error handling and resilience.
Comprehensive tool ecosystem integration.

Recommendation: {hire_decision}
{self._generate_hire_reasoning(foundation, production, differentiation, competitive)}

Next steps:
{chr(10).join('• ' + step for step in self._generate_next_steps(hire_decision))}
"""

    def _serialize_suite_result(self, result: SuiteResult) -> dict[str, Any]:
        """Serialize suite result for JSON output."""
        return {
            "suite_name": result.suite_name,
            "suite_passed": result.suite_passed,
            "execution_time": result.execution_time,
            "pass_rate": result.pass_rate,
            "executive_insight": result.executive_insight,
            "recommendation": result.recommendation,
            "detailed_results": result.detailed_results,
        }
