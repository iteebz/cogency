"""Demo Flow Orchestrator - Strategic AGI Lab Evaluation Sequence

Organizes evaluations by strategic impact rather than technical category.
Implements progressive disclosure with early exit opportunities.
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class TierResult:
    """Result from a strategic evaluation tier."""

    tier_name: str
    tier_passed: bool
    execution_time: float
    pass_rate: float
    key_metrics: dict[str, Any]
    executive_summary: str
    risk_flags: list[str]
    recommendation: str


class DemoFlowOrchestrator:
    """Orchestrate strategic evaluation flow for maximum AGI lab impact."""

    def __init__(self):
        self.tier_definitions = self._define_strategic_tiers()
        self.results = []

    def _define_strategic_tiers(self) -> dict[str, dict[str, Any]]:
        """Define the four strategic evaluation tiers."""
        return {
            "foundation": {
                "name": "Foundation Competence",
                "description": "Basic functionality - does Cogency work at all?",
                "time_budget": 180,  # 3 minutes
                "pass_threshold": 0.9,  # 90% must pass
                "early_exit_on_failure": True,
                "evaluations": [
                    # Import and instantiate basic evaluations
                    "basic_agent_function",
                    "basic_tool_usage",
                    "basic_memory",
                    "basic_security",
                ],
            },
            "differentiation": {
                "name": "Competitive Differentiation",
                "description": "Unique capabilities - what makes Cogency special?",
                "time_budget": 900,  # 15 minutes
                "pass_threshold": 0.7,  # 70% to show compelling differentiation
                "early_exit_on_failure": False,  # Still valuable to see production readiness
                "evaluations": [
                    "cross_session_workflows",
                    "tool_orchestration",
                    "error_resilience",
                    "workflow_state_management",
                ],
            },
            "production": {
                "name": "Production Readiness",
                "description": "Enterprise deployment safety - can this be trusted?",
                "time_budget": 720,  # 12 minutes
                "pass_threshold": 0.8,  # 80% for production confidence
                "early_exit_on_failure": False,
                "evaluations": [
                    "security_hardening",
                    "error_boundaries",
                    "resource_constraints",
                    "concurrent_safety",
                ],
            },
            "benchmarking": {
                "name": "Industry Benchmarking",
                "description": "Competitive positioning - how does this compare?",
                "time_budget": 1200,  # 20 minutes
                "pass_threshold": 0.5,  # 50% competitive performance
                "early_exit_on_failure": False,
                "evaluations": ["swe_bench_lite", "gaia_authentic"],
            },
        }

    async def execute_strategic_evaluation(
        self, early_exit: bool = True, tier_filter: Optional[list[str]] = None
    ) -> dict[str, Any]:
        """Execute strategic evaluation with progressive disclosure."""

        print("🎯 STRATEGIC AGI LAB EVALUATION - PROGRESSIVE DISCLOSURE")
        print("=" * 70)

        start_time = time.time()
        overall_recommendation = "CONTINUE_EVALUATION"

        # Execute tiers in strategic order
        tier_order = ["foundation", "differentiation", "production", "benchmarking"]
        if tier_filter:
            tier_order = [t for t in tier_order if t in tier_filter]

        for tier_name in tier_order:
            tier_def = self.tier_definitions[tier_name]

            print(f"\n🔍 TIER {len(self.results) + 1}: {tier_def['name'].upper()}")
            print(f"   {tier_def['description']}")
            print(
                f"   Time Budget: {tier_def['time_budget']}s | Pass Threshold: {tier_def['pass_threshold']:.0%}"
            )
            print("-" * 50)

            # Execute tier
            tier_result = await self._execute_tier(tier_name, tier_def)
            self.results.append(tier_result)

            # Report tier results
            self._report_tier_results(tier_result)

            # Early exit decision
            if early_exit and tier_result.tier_passed is False:
                if tier_def["early_exit_on_failure"]:
                    overall_recommendation = "TERMINATE_EVALUATION"
                    print(f"\n🚨 EARLY EXIT: {tier_result.tier_name} failed critical threshold")
                    break
                if tier_name == "differentiation" and tier_result.pass_rate < 0.5:
                    overall_recommendation = "WEAK_DIFFERENTIATION"
                    print("\n⚠️ WEAK DIFFERENTIATION: Consider continuing but value unclear")

        # Generate final assessment
        total_time = time.time() - start_time
        final_assessment = self._generate_final_assessment(overall_recommendation, total_time)

        return {
            "strategic_evaluation_complete": True,
            "execution_time": total_time,
            "tier_results": self.results,
            "final_assessment": final_assessment,
            "recommendation": overall_recommendation,
        }

    async def _execute_tier(self, tier_name: str, tier_def: dict[str, Any]) -> TierResult:
        """Execute a single strategic tier."""
        tier_start = time.time()

        # Mock execution for now - replace with actual evaluation calls
        # TODO: Replace with actual evaluation instantiation and execution
        await asyncio.sleep(1)  # Simulate evaluation time

        # Mock results - replace with real evaluation aggregation
        mock_pass_rate = 0.85  # This would come from actual evaluations
        tier_passed = mock_pass_rate >= tier_def["pass_threshold"]

        execution_time = time.time() - tier_start

        # Generate tier-specific insights
        key_metrics = self._generate_tier_metrics(tier_name, mock_pass_rate)
        executive_summary = self._generate_executive_summary(tier_name, mock_pass_rate, tier_passed)
        risk_flags = self._identify_risk_flags(tier_name, mock_pass_rate)
        recommendation = self._generate_tier_recommendation(tier_name, tier_passed, mock_pass_rate)

        return TierResult(
            tier_name=tier_def["name"],
            tier_passed=tier_passed,
            execution_time=execution_time,
            pass_rate=mock_pass_rate,
            key_metrics=key_metrics,
            executive_summary=executive_summary,
            risk_flags=risk_flags,
            recommendation=recommendation,
        )

    def _generate_tier_metrics(self, tier_name: str, pass_rate: float) -> dict[str, Any]:
        """Generate tier-specific key metrics."""
        metrics = {
            "foundation": {
                "basic_functionality": f"{pass_rate:.1%}",
                "critical_failures": 0 if pass_rate > 0.9 else 1,
                "readiness_for_advanced_eval": pass_rate > 0.8,
            },
            "differentiation": {
                "unique_capability_strength": f"{pass_rate:.1%}",
                "competitive_moat_width": "Strong"
                if pass_rate > 0.8
                else "Moderate"
                if pass_rate > 0.6
                else "Weak",
                "market_differentiation": pass_rate > 0.7,
            },
            "production": {
                "deployment_safety": f"{pass_rate:.1%}",
                "enterprise_readiness": pass_rate > 0.8,
                "risk_mitigation_coverage": f"{min(pass_rate * 1.1, 1.0):.1%}",
            },
            "benchmarking": {
                "industry_competitiveness": f"{pass_rate:.1%}",
                "market_positioning": "Leading"
                if pass_rate > 0.8
                else "Competitive"
                if pass_rate > 0.6
                else "Lagging",
                "benchmark_credibility": pass_rate > 0.5,
            },
        }
        return metrics.get(tier_name, {})

    def _generate_executive_summary(
        self, tier_name: str, pass_rate: float, tier_passed: bool
    ) -> str:
        """Generate executive-friendly tier summary."""
        summaries = {
            "foundation": f"Basic functionality {'✅ CONFIRMED' if tier_passed else '❌ INSUFFICIENT'} - {pass_rate:.1%} core capabilities operational",
            "differentiation": f"Competitive advantage {'✅ DEMONSTRATED' if tier_passed else '⚠️ UNCLEAR'} - {pass_rate:.1%} unique capabilities performing well",
            "production": f"Enterprise deployment {'✅ READY' if tier_passed else '⚠️ RISKY'} - {pass_rate:.1%} production safety checks passed",
            "benchmarking": f"Market competitiveness {'✅ PROVEN' if tier_passed else '📊 MEASURED'} - {pass_rate:.1%} performance on industry benchmarks",
        }
        return summaries.get(tier_name, f"Tier performance: {pass_rate:.1%}")

    def _identify_risk_flags(self, tier_name: str, pass_rate: float) -> list[str]:
        """Identify tier-specific risk flags."""
        flags = []

        if tier_name == "foundation" and pass_rate < 0.9:
            flags.append("BASIC_FUNCTIONALITY_GAPS")
        if tier_name == "differentiation" and pass_rate < 0.6:
            flags.append("WEAK_COMPETITIVE_MOAT")
        if tier_name == "production" and pass_rate < 0.7:
            flags.append("DEPLOYMENT_RISKS")
        if tier_name == "benchmarking" and pass_rate < 0.4:
            flags.append("UNCOMPETITIVE_PERFORMANCE")

        return flags

    def _generate_tier_recommendation(
        self, tier_name: str, tier_passed: bool, pass_rate: float
    ) -> str:
        """Generate tier-specific recommendation."""
        if not tier_passed:
            return f"INVESTIGATE_{tier_name.upper()}_FAILURES"
        if pass_rate > 0.9:
            return f"{tier_name.upper()}_EXCEEDS_EXPECTATIONS"
        return f"{tier_name.upper()}_MEETS_STANDARDS"

    def _report_tier_results(self, result: TierResult):
        """Report tier results with executive summary."""
        status_emoji = "✅" if result.tier_passed else "❌"
        print(
            f"\n{status_emoji} {result.tier_name.upper()}: {result.pass_rate:.1%} ({result.execution_time:.1f}s)"
        )
        print(f"   📊 {result.executive_summary}")

        if result.risk_flags:
            print(f"   🚨 Risk Flags: {', '.join(result.risk_flags)}")

        print(f"   💡 Recommendation: {result.recommendation}")

    def _generate_final_assessment(self, recommendation: str, total_time: float) -> dict[str, Any]:
        """Generate final strategic assessment."""

        # Calculate tier performance summary
        tier_performance = {}
        for result in self.results:
            tier_performance[result.tier_name.lower().replace(" ", "_")] = {
                "passed": result.tier_passed,
                "pass_rate": result.pass_rate,
                "time": result.execution_time,
            }

        # Overall hiring recommendation logic
        foundation_passed = tier_performance.get("foundation_competence", {}).get("passed", False)
        differentiation_rate = tier_performance.get("competitive_differentiation", {}).get(
            "pass_rate", 0.0
        )
        production_passed = tier_performance.get("production_readiness", {}).get("passed", False)

        if not foundation_passed:
            hire_recommendation = "DO_NOT_HIRE"
        elif differentiation_rate > 0.8 and production_passed:
            hire_recommendation = "STRONG_HIRE"
        elif differentiation_rate > 0.6:
            hire_recommendation = "HIRE_WITH_CONDITIONS"
        else:
            hire_recommendation = "WEAK_HIRE"

        return {
            "overall_execution_time": f"{total_time:.1f}s",
            "tiers_completed": len(self.results),
            "tier_performance": tier_performance,
            "strategic_recommendation": recommendation,
            "hiring_recommendation": hire_recommendation,
            "key_insights": self._extract_key_insights(),
            "next_steps": self._recommend_next_steps(hire_recommendation),
        }

    def _extract_key_insights(self) -> list[str]:
        """Extract key insights from tier results."""
        insights = []

        for result in self.results:
            if result.pass_rate > 0.9:
                insights.append(f"Exceptional {result.tier_name.lower()} performance")
            elif not result.tier_passed:
                insights.append(f"{result.tier_name} requires attention")

        return insights

    def _recommend_next_steps(self, hire_recommendation: str) -> list[str]:
        """Recommend next steps based on evaluation results."""
        next_steps = {
            "STRONG_HIRE": [
                "Proceed with technical deep-dive interviews",
                "Discuss specific project alignment",
                "Prepare offer package",
            ],
            "HIRE_WITH_CONDITIONS": [
                "Address identified gaps in follow-up evaluation",
                "Discuss remediation timeline",
                "Consider probationary period",
            ],
            "WEAK_HIRE": [
                "Provide detailed feedback on weaknesses",
                "Suggest improvement areas",
                "Reconsider after development period",
            ],
            "DO_NOT_HIRE": [
                "End evaluation process",
                "Provide constructive feedback",
                "Keep in talent pipeline for future roles",
            ],
        }
        return next_steps.get(hire_recommendation, ["Continue standard evaluation process"])
