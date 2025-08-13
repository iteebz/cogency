#!/usr/bin/env python3
"""Run Cogency Showcase Evaluation - AGI Lab Demo

Execute the comprehensive Cogency capability showcase for Anthropic job application.
Demonstrates unique differentiators and public benchmark performance.

Usage:
    python -m evals.run_showcase

    # Or with custom sample sizes for cost control
    python -m evals.run_showcase --memory 20 --orchestration 20 --resilience 10
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .showcase import CogencyShowcase


def print_executive_summary(report: dict):
    """Print executive summary for quick assessment."""
    exec_summary = report.get("executive_summary", {})

    print("\n" + "=" * 60)
    print("🎯 COGENCY SHOWCASE - EXECUTIVE SUMMARY")
    print("=" * 60)

    print(f"Overall Assessment: {exec_summary.get('overall_assessment', 'UNKNOWN')}")
    print(f"Total Test Coverage: {exec_summary.get('total_test_coverage', 'N/A')}")

    print("\n📊 UNIQUE VALUE PROPOSITION:")
    uvp = exec_summary.get("unique_value_proposition", {})
    for capability, performance in uvp.items():
        print(f"  • {capability.replace('_', ' ').title()}: {performance}")

    print("\n🏆 INDUSTRY BENCHMARK CREDIBILITY:")
    benchmark = exec_summary.get("industry_benchmark_credibility", {})
    for benchmark_name, performance in benchmark.items():
        print(f"  • {benchmark_name.replace('_', ' ').upper()}: {performance}")

    print("\n🔧 TECHNICAL SOPHISTICATION:")
    tech = report.get("technical_sophistication", {})
    for aspect, detail in tech.items():
        print(f"  • {aspect.replace('_', ' ').title()}: {detail}")

    print("\n💡 RECOMMENDATION FOR ANTHROPIC:")
    rec = report.get("recommendation_for_anthropic", {})
    for criteria, assessment in rec.items():
        print(f"  • {criteria.replace('_', ' ').title()}: {assessment}")


async def main():
    """Execute Cogency showcase evaluation."""
    parser = argparse.ArgumentParser(description="Run Cogency Showcase Evaluation")
    parser.add_argument(
        "--memory", type=int, default=25, help="Memory workflow samples (default: 25)"
    )
    parser.add_argument(
        "--orchestration", type=int, default=25, help="Tool orchestration samples (default: 25)"
    )
    parser.add_argument(
        "--resilience", type=int, default=15, help="Error resilience samples (default: 15)"
    )
    parser.add_argument("--swe", type=int, default=30, help="SWE-bench samples (default: 30)")
    parser.add_argument("--gaia", type=int, default=20, help="GAIA samples (default: 20)")
    parser.add_argument("--output", type=str, help="Save results to JSON file")
    parser.add_argument("--quick", action="store_true", help="Quick demo mode (fewer samples)")

    args = parser.parse_args()

    # Quick mode for fast demos
    if args.quick:
        print("🚀 QUICK DEMO MODE - Reduced sample sizes for fast evaluation")
        args.memory = 5
        args.orchestration = 5
        args.resilience = 5
        args.swe = 10
        args.gaia = 5

    print("🧪 COGENCY SHOWCASE EVALUATION")
    print(
        f"Sample sizes: Memory={args.memory}, Orchestration={args.orchestration}, Resilience={args.resilience}"
    )
    print(f"Benchmarks: SWE={args.swe}, GAIA={args.gaia}")
    print(
        f"Total test budget: {args.memory + args.orchestration + args.resilience + args.swe + args.gaia}"
    )

    # Create and execute showcase
    showcase = CogencyShowcase(
        memory_samples=args.memory,
        orchestration_samples=args.orchestration,
        resilience_samples=args.resilience,
        swe_samples=args.swe,
        gaia_samples=args.gaia,
    )

    try:
        result = await showcase.execute()

        # Print executive summary
        agi_report = result.get("agi_lab_report", {})
        print_executive_summary(agi_report)

        # Show overall results
        print(
            f"\n🎯 SHOWCASE RESULT: {'✅ PASSED' if result.get('showcase_passed', False) else '❌ FAILED'}"
        )
        print(f"⏱️ Duration: {result.get('duration', 0):.1f} seconds")
        print(
            f"📈 Overall Pass Rate: {result.get('summary', {}).get('overall_pass_rate', 0.0):.1%}"
        )

        # Save results if requested
        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"💾 Results saved to {output_path}")

        # Exit with success/failure code
        sys.exit(0 if result.get("showcase_passed", False) else 1)

    except Exception as e:
        print(f"❌ SHOWCASE EXECUTION FAILED: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())
