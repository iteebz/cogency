"""Tool performance microbench - measure local tool execution overhead."""

import asyncio
import contextlib
import statistics
import tracemalloc
from time import perf_counter
from typing import Dict, List, Tuple

from cogency.tools.files import Files
from cogency.tools.shell import Shell

from ..eval import Eval


class ToolPerformance(Eval):
    """Measure local tool invocation latency and orchestration overhead."""

    name = "tool_performance"
    description = "Tool execution latency microbenchmark"

    async def run(self) -> Dict:
        tracemalloc.start()
        mem_before = tracemalloc.get_traced_memory()[0]

        # Setup: create test file for read operations
        setup_files = Files()
        with contextlib.suppress(Exception):
            await setup_files.run(action="write", path="bench_test.txt", content="test")

        # Declarative test cases for performance benchmarks
        test_cases = [
            {
                "name": "Shell echo latency <100ms",
                "tool": Shell(),
                "args": {"command": "echo 'benchmark'"},
                "iterations": 10,
            },
            {
                "name": "Files write latency <100ms",
                "tool": Files(),
                "args": {"action": "write", "path": "bench_test.txt", "content": "test"},
                "iterations": 10,
            },
            {
                "name": "Files read latency <100ms",
                "tool": Files(),
                "args": {"action": "read", "path": "bench_test.txt"},
                "iterations": 10,
            },
        ]

        perf_results = []
        validation_failures = 0
        all_traces = []

        # Run test cases
        for case in test_cases:
            try:
                times, validation_errors = await self._benchmark_tool(case)
                validation_failures += validation_errors

                if times:
                    mean_time = statistics.mean(times)
                    passed = mean_time * 1000 < 100 and validation_errors == 0
                    perf_results.append(
                        {
                            "test_name": case["name"],
                            "mean_ms": mean_time * 1000,
                            "validation_errors": validation_errors,
                            "passed": passed,
                        }
                    )
                else:
                    passed = False
                    perf_results.append(
                        {
                            "test_name": case["name"],
                            "mean_ms": float("inf"),
                            "validation_errors": validation_errors,
                            "passed": passed,
                        }
                    )

                all_traces.append(
                    {
                        "test_case": case["name"],
                        "passed": passed,
                        "mean_latency_ms": perf_results[-1]["mean_ms"],
                        "validation_errors": validation_errors,
                    }
                )

            except Exception as e:
                all_traces.append(
                    {
                        "test_case": case["name"],
                        "passed": False,
                        "error": str(e),
                    }
                )

        mem_after = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        # Calculate overall metrics
        mem_delta_mb = (mem_after - mem_before) / 1024 / 1024
        valid_results = [r["mean_ms"] for r in perf_results if r["mean_ms"] != float("inf")]
        avg_latency = statistics.mean(valid_results) if valid_results else float("inf")
        total_ops = sum(tc["iterations"] for tc in test_cases)
        validation_accuracy = 1.0 - (validation_failures / total_ops) if total_ops > 0 else 1.0

        passed_count = sum(1 for r in perf_results if r["passed"])
        score = passed_count / len(test_cases) if test_cases else 0.0
        passed = score >= 0.67

        return {
            "name": self.name,
            "passed": passed,
            "score": score,
            "duration": 0.0,
            "traces": all_traces,
            "metadata": {
                "avg_latency_ms": avg_latency,
                "validation_accuracy": validation_accuracy,
                "memory_delta_mb": mem_delta_mb,
                "individual_results": perf_results,
            },
        }

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
