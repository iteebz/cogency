"""Tool performance microbench - measure local tool execution overhead."""

import asyncio
import contextlib
import statistics
import tracemalloc
from time import perf_counter
from typing import List, Tuple

from cogency.tools.files import Files
from cogency.tools.shell import Shell

from ...core import Eval, EvalResult, FailureType


class ToolPerformance(Eval):
    """Measure local tool invocation latency and orchestration overhead."""

    name = "tool_performance"
    description = "Tool execution latency microbenchmark"

    # Declarative test cases for performance benchmarks
    test_cases = [
        {
            "name": "Shell echo latency <100ms",
            "tool": Shell(),
            "args": {"command": "echo 'benchmark'"},
            "iterations": 10,
            "expected": True,
            "parser": "_check_latency",
        },
        {
            "name": "Files write latency <100ms",
            "tool": Files(),
            "args": {"action": "write", "path": "bench_test.txt", "content": "test"},
            "iterations": 10,
            "expected": True,
            "parser": "_check_latency",
        },
        {
            "name": "Files read latency <100ms",
            "tool": Files(),
            "args": {"action": "read", "path": "bench_test.txt"},
            "iterations": 10,
            "expected": True,
            "parser": "_check_latency",
        },
    ]

    async def run(self) -> EvalResult:
        """Run performance tests using declarative test cases."""

        tracemalloc.start()
        mem_before = tracemalloc.get_traced_memory()[0]

        # Setup: create test file for read operations
        setup_files = Files()
        with contextlib.suppress(Exception):
            await setup_files.run(action="write", path="bench_test.txt", content="test")

        # Track performance data for overall metrics
        self._perf_results = []
        self._validation_failures = 0

        # Run declarative test cases
        for case in self.test_cases:
            try:
                times, validation_errors = await self._benchmark_tool(case)
                self._validation_failures += validation_errors

                if times:
                    mean_time = statistics.mean(times)
                    passed = mean_time * 1000 < 100 and validation_errors == 0
                    self._perf_results.append(
                        {
                            "test_name": case["name"],
                            "mean_ms": mean_time * 1000,
                            "validation_errors": validation_errors,
                            "passed": passed,
                        }
                    )
                else:
                    passed = False
                    self._perf_results.append(
                        {
                            "test_name": case["name"],
                            "mean_ms": float("inf"),
                            "validation_errors": validation_errors,
                            "passed": passed,
                        }
                    )

                self.check_sub_case(case["name"], passed, case["expected"])

            except Exception as e:
                self.fail_sub_case(case["name"], f"benchmark error: {e}", FailureType.ERROR)

        mem_after = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        # Calculate overall metrics for metadata
        mem_delta_mb = (mem_after - mem_before) / 1024 / 1024
        avg_latency = statistics.mean(
            [r["mean_ms"] for r in self._perf_results if r["mean_ms"] != float("inf")]
        )
        total_ops = sum(tc["iterations"] for tc in self.test_cases)
        validation_accuracy = (
            1.0 - (self._validation_failures / total_ops) if total_ops > 0 else 1.0
        )

        metadata = {
            "avg_latency_ms": avg_latency,
            "validation_accuracy": validation_accuracy,
            "memory_delta_mb": mem_delta_mb,
            "individual_results": self._perf_results,
        }

        return self.finalize_result(metadata)

    def _check_latency(self, case: dict) -> bool:
        """Parser for latency checks - actual logic is in run()."""
        # This parser is called from the main loop, but the actual
        # latency checking is done in run() method for performance reasons
        return case.get("passed", False)

    async def _benchmark_tool(self, test_case: dict) -> Tuple[List[float], int]:
        """Benchmark tool execution with validation."""
        times = []
        validation_errors = 0
        tool = test_case["tool"]
        args = test_case["args"]

        for _i in range(test_case["iterations"]):
            try:
                start = perf_counter()
                result = await tool.run(**args)
                end = perf_counter()

                # Validate result - tools should return some result
                if result is None:
                    validation_errors += 1

                times.append(end - start)

                # Small delay between iterations
                await asyncio.sleep(0.01)

            except Exception:
                validation_errors += 1
                times.append(0.1)  # Penalty time

        return times, validation_errors
