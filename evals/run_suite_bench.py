"""Run eval suites with detailed benchmarking - performance analysis of cogency evaluations."""

import asyncio
import sys

from suite import COGENCY_SUITE, PROVIDER_SUITE, QUICK_SUITE

from cogency.evals.runner import run_suite_benchmarked


async def main():
    """Run the specified eval suite with benchmarking."""
    if len(sys.argv) < 2:
        print("Usage: python run_suite_bench.py [quick|provider|full]")
        sys.exit(1)

    suite_name = sys.argv[1].lower()

    if suite_name == "quick":
        suite = QUICK_SUITE
    elif suite_name == "provider":
        suite = PROVIDER_SUITE
    elif suite_name == "full":
        suite = COGENCY_SUITE
    else:
        print(f"Unknown suite: {suite_name}")
        print("Available suites: quick, provider, full")
        sys.exit(1)

    print(f"🔥 Benchmarking {suite_name} eval suite ({len(suite)} evals)")
    print()

    # Run the suite with benchmarking
    report = await run_suite_benchmarked(suite)

    # Beautiful console output
    print(report.console())

    # Quick benchmark summary
    if report.benchmarks:
        print("\n📊 Performance Summary:")
        total_phases = sum(
            len(b["phase_timing"]["phases"]) for b in report.benchmarks if b["phase_timing"]
        )
        print(f"   Total phases executed: {total_phases}")

        # Show slowest phases
        all_phases = []
        for benchmark in report.benchmarks:
            if benchmark["phase_timing"] and benchmark["phase_timing"]["phases"]:
                for phase in benchmark["phase_timing"]["phases"]:
                    all_phases.append((phase["phase"], phase["duration"]))

        if all_phases:
            all_phases.sort(key=lambda x: x[1], reverse=True)
            print(f"   Slowest phase: {all_phases[0][0]} ({all_phases[0][1]:.2f}s)")


if __name__ == "__main__":
    asyncio.run(main())
