#!/usr/bin/env python3
"""Cogency Evaluation Demo

Usage:
    python -m evals.demo
    python -m evals.demo --suites foundation,production
    python -m evals.demo --no-early-exit --output results.json
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

from .evaluator import Evaluator


def print_header():
    """Print evaluation header."""
    print("\n🧠 Cogency Evaluation")
    print("Foundation → Production → Differentiation → Benchmarking")
    print()


def print_suites():
    """Print evaluation suites."""
    print("🏛️ Foundation - Basic functionality")
    print("🛡️ Production - Resilience and error handling")
    print("🚀 Differentiation - Unique capabilities")
    print("📊 Benchmarking - Competitive performance")
    print()


def print_summary(assessment: dict):
    """Print evaluation summary."""
    exec_summary = assessment.get("executive_summary", "")

    print("\n" + "=" * 50)
    print("📋 EVALUATION SUMMARY")
    print("=" * 50)
    print(exec_summary)
    print("=" * 50)


def print_recommendation(assessment: dict):
    """Print recommendation."""
    strategic = assessment.get("strategic_recommendation", {})

    print(f"\nDecision: {strategic.get('hire_decision', 'UNKNOWN')}")
    print(f"Reasoning: {strategic.get('reasoning', 'No reasoning provided')}")

    next_steps = strategic.get("next_steps", [])
    if next_steps:
        print("\nNext steps:")
        for step in next_steps:
            print(f"  • {step}")


async def main():
    """Execute Cogency evaluation."""
    parser = argparse.ArgumentParser(
        description="Cogency Evaluation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m evals.demo                       # Full evaluation
  python -m evals.demo --suites foundation  # Foundation only
  python -m evals.demo --no-early-exit      # Complete all suites
  python -m evals.demo --output demo.json   # Save results
        """,
    )

    parser.add_argument(
        "--suites",
        type=str,
        help="Comma-separated suites to run (foundation,production,differentiation,benchmarking)",
    )
    parser.add_argument(
        "--no-early-exit",
        action="store_true",
        help="Continue evaluation even after critical failures",
    )
    parser.add_argument("--output", type=str, help="Save detailed results to JSON file")
    parser.add_argument(
        "--quiet", action="store_true", help="Minimal output - executive summary only"
    )

    args = parser.parse_args()

    # Parse suites filter
    suites_filter = None
    if args.suites:
        suites_filter = [suite.strip() for suite in args.suites.split(",")]

    # Print headers unless quiet
    if not args.quiet:
        print_header()
        print_suites()

    print("🚀 Starting evaluation...")

    # Create and execute evaluator
    evaluator = Evaluator()

    try:
        result = await evaluator.execute_evaluation(
            early_exit=not args.no_early_exit, suites_filter=suites_filter
        )

        # Extract final assessment
        final_assessment = result.get("final_assessment", {})

        # Print summary and recommendation
        print_summary(final_assessment)
        print_recommendation(final_assessment)

        # Show overall result
        overall_rec = result.get("overall_recommendation", "UNKNOWN")
        print(f"\nResult: {overall_rec}")
        print(f"Duration: {result.get('total_execution_time', 0):.1f}s")
        print(f"Suites: {result.get('suites_completed', 0)}")

        # Save detailed results if requested
        if args.output:
            output_path = Path(args.output)
            with open(output_path, "w") as f:
                json.dump(result, f, indent=2, default=str)
            print(f"Results saved to {output_path}")

        # Exit with appropriate code for CI/automation
        hire_decision = final_assessment.get("strategic_recommendation", {}).get(
            "hire_decision", "DO_NOT_HIRE"
        )
        if hire_decision in ["STRONG_HIRE", "HIRE"]:
            sys.exit(0)
        elif hire_decision == "WEAK_HIRE":
            sys.exit(1)
        else:
            sys.exit(2)

    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)

    except Exception as e:
        print(f"\nFailed: {e}")
        if not args.quiet:
            import traceback

            traceback.print_exc()
        sys.exit(3)


if __name__ == "__main__":
    asyncio.run(main())
