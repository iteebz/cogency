"""Evaluation runner with CI integration."""

import asyncio
import sys
import time
from typing import Any

from .internal.memory import CrossSessionMemory, MemoryInterference, TemporalOrdering
from .logging import EvalLogger
from .security import InjectionResistance
from .tools import ToolIntegration


class EvaluationRunner:
    """Main evaluation runner for CI integration."""

    def __init__(self):
        self.logger = EvalLogger()
        self.available_benchmarks = {
            # Sophisticated memory benchmarks (competitive differentiator)
            "cross_session": CrossSessionMemory,
            "temporal": TemporalOrdering,
            "interference": MemoryInterference,
            # Core capability evaluations for current cogency
            "security": InjectionResistance,
            "tools": ToolIntegration,
        }

    async def run_benchmark(self, benchmark_name: str) -> dict[str, Any]:
        """Run single benchmark."""
        if benchmark_name not in self.available_benchmarks:
            raise ValueError(f"Unknown benchmark: {benchmark_name}")

        benchmark_class = self.available_benchmarks[benchmark_name]
        benchmark = benchmark_class()

        print(f"🧠 Running {benchmark.name} benchmark...")
        start_time = time.time()

        try:
            result = await benchmark.execute()
            duration = time.time() - start_time
            result["duration"] = duration

            # Report status
            if result.get("summary", {}).get("benchmark_passed", False):
                print(f"✅ {benchmark.name} PASSED ({duration:.1f}s)")
            else:
                print(f"❌ {benchmark.name} FAILED ({duration:.1f}s)")

            return result

        except Exception as e:
            duration = time.time() - start_time
            print(f"💥 {benchmark.name} ERROR: {e} ({duration:.1f}s)")
            return {
                "name": benchmark.name,
                "error": str(e),
                "duration": duration,
                "benchmark_passed": False,
            }

    async def run_memory_suite(self) -> dict[str, Any]:
        """Run complete memory benchmark suite."""
        print("🧠 Running Cogency Memory Benchmark Suite")
        print("=" * 50)

        suite_start = time.time()
        results = []

        # Sophisticated memory benchmarks (competitive differentiators)
        memory_benchmarks = ["cross_session", "temporal", "interference"]
        for benchmark_name in memory_benchmarks:
            result = await self.run_benchmark(benchmark_name)
            results.append(result)
            print()  # Spacing between benchmarks

        # Calculate suite summary
        suite_duration = time.time() - suite_start
        passed_benchmarks = sum(1 for r in results if r.get("benchmark_passed", False))
        total_benchmarks = len(results)
        suite_success = passed_benchmarks == total_benchmarks

        suite_report = {
            "suite_name": "Memory Benchmark Suite",
            "timestamp": time.time(),
            "duration": suite_duration,
            "benchmarks": results,
            "summary": {
                "total_benchmarks": total_benchmarks,
                "passed_benchmarks": passed_benchmarks,
                "suite_success": suite_success,
                "pass_rate": passed_benchmarks / total_benchmarks if total_benchmarks > 0 else 0.0,
            },
        }

        # Print suite summary
        print("=" * 50)
        print("📊 SUITE SUMMARY")
        print(f"Passed: {passed_benchmarks}/{total_benchmarks} benchmarks")
        print(f"Duration: {suite_duration:.1f}s")

        if suite_success:
            print("🎉 MEMORY SUITE PASSED")
        else:
            print("💀 MEMORY SUITE FAILED")

        return suite_report

    async def run_capability_suite(self) -> dict[str, Any]:
        """Run evaluations matching current cogency capabilities."""
        print("🔍 Running Capability Evaluation Suite")
        print("=" * 50)

        suite_start = time.time()
        results = []

        # Test current capabilities: security, tools
        capability_benchmarks = ["security", "tools"]
        for benchmark_name in capability_benchmarks:
            result = await self.run_benchmark(benchmark_name)
            results.append(result)
            print()

        suite_duration = time.time() - suite_start
        passed_benchmarks = sum(1 for r in results if r.get("benchmark_passed", False))
        total_benchmarks = len(results)
        suite_success = passed_benchmarks == total_benchmarks

        suite_report = {
            "suite_name": "Capability Evaluation Suite",
            "timestamp": time.time(),
            "duration": suite_duration,
            "benchmarks": results,
            "summary": {
                "total_benchmarks": total_benchmarks,
                "passed_benchmarks": passed_benchmarks,
                "suite_success": suite_success,
                "pass_rate": passed_benchmarks / total_benchmarks if total_benchmarks > 0 else 0.0,
            },
        }

        # Print suite summary
        print("=" * 50)
        print("📊 CAPABILITY SUITE SUMMARY")
        print(f"Passed: {passed_benchmarks}/{total_benchmarks} benchmarks")
        print(f"Duration: {suite_duration:.1f}s")

        if suite_success:
            print("🎉 CAPABILITY SUITE PASSED")
        else:
            print("💀 CAPABILITY SUITE FAILED")

        return suite_report

    async def run_all(self) -> dict[str, Any]:
        """Run all available evaluations (both competitive and capability)."""
        print("🚀 Running Complete Evaluation Suite")
        print("=" * 60)

        suite_start = time.time()

        # Run both capability tests and competitive differentiators
        capability_results = await self.run_capability_suite()
        print("\n" + "=" * 60)
        memory_results = await self.run_memory_suite()

        # Combine results
        all_benchmarks = capability_results["benchmarks"] + memory_results["benchmarks"]
        total_duration = time.time() - suite_start
        passed_benchmarks = sum(1 for r in all_benchmarks if r.get("benchmark_passed", False))
        total_benchmarks = len(all_benchmarks)
        overall_success = passed_benchmarks == total_benchmarks

        combined_report = {
            "suite_name": "Complete Evaluation Suite",
            "timestamp": time.time(),
            "duration": total_duration,
            "capability_results": capability_results,
            "memory_results": memory_results,
            "summary": {
                "total_benchmarks": total_benchmarks,
                "passed_benchmarks": passed_benchmarks,
                "overall_success": overall_success,
                "pass_rate": passed_benchmarks / total_benchmarks if total_benchmarks > 0 else 0.0,
            },
        }

        print("\n" + "=" * 60)
        print("📊 OVERALL SUMMARY")
        print(f"Passed: {passed_benchmarks}/{total_benchmarks} total benchmarks")
        print(f"Duration: {total_duration:.1f}s")

        if overall_success:
            print("🏆 ALL EVALUATIONS PASSED")
        else:
            print("💀 SOME EVALUATIONS FAILED")

        return combined_report


async def main():
    """CLI entry point for evaluation runner."""
    runner = EvaluationRunner()

    if len(sys.argv) < 2:
        print("Usage: python -m evals.runner [memory|capability|security|tools|all|benchmark_name]")
        print()
        print("Test suites:")
        print("  memory: Advanced memory benchmarks (competitive differentiator)")
        print("  capability: Current cogency capability tests")
        print("  all: Complete evaluation suite")
        print()
        print("Individual benchmarks:")
        for name, cls in runner.available_benchmarks.items():
            print(f"  {name}: {cls.description}")
        sys.exit(1)

    target = sys.argv[1].lower()

    try:
        if target == "memory":
            result = await runner.run_memory_suite()
        elif target == "capability":
            result = await runner.run_capability_suite()
        elif target == "all":
            result = await runner.run_all()
        elif target in runner.available_benchmarks:
            result = await runner.run_benchmark(target)
        else:
            print(f"Unknown target: {target}")
            sys.exit(1)

        # Exit with appropriate code for CI
        success = result.get("suite_success") or result.get("benchmark_passed", False)
        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"💥 Evaluation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
