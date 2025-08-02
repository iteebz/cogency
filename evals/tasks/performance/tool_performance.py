"""Tool performance microbench - measure tool execution overhead."""

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
    """Measure tool invocation latency and orchestration overhead."""

    name = "tool_performance"
    description = "Tool execution latency microbenchmark"

    async def run(self) -> EvalResult:
        """Run performance tests on canonical 5-tool architecture."""

        tracemalloc.start()
        mem_before = tracemalloc.get_traced_memory()[0]

        test_cases = [
            {
                "name": "shell_echo",
                "tool": Shell(),
                "args": {"command": "echo 'benchmark'"},
                "iterations": 10,
            },
            {
                "name": "files_write",
                "tool": Files(),
                "args": {"action": "write", "path": "bench_test.txt", "content": "test"},
                "iterations": 10,
            },
            {
                "name": "files_read",
                "tool": Files(),
                "args": {"action": "read", "path": "bench_test.txt"},
                "iterations": 10,
            },
        ]

        # Setup: create test file for read operations
        setup_files = Files()
        with contextlib.suppress(Exception):
            await setup_files.run(action="write", path="bench_test.txt", content="test")

        results = []
        validation_failures = 0

        for test_case in test_cases:
            times, validation_errors = await self._benchmark_tool(test_case)
            validation_failures += validation_errors

            if times:
                mean_time = statistics.mean(times)
                p95_time = statistics.quantiles(times, n=20)[18] if len(times) >= 5 else mean_time
                passed = mean_time * 1000 < 100 and validation_errors == 0
            else:
                mean_time = float("inf")
                p95_time = float("inf")
                passed = False

            results.append(
                {
                    "test_name": test_case["name"],
                    "mean_ms": mean_time * 1000,
                    "p95_ms": p95_time * 1000,
                    "validation_errors": validation_errors,
                    "passed": passed,
                }
            )

        mem_after = tracemalloc.get_traced_memory()[0]
        tracemalloc.stop()

        mem_delta_mb = (mem_after - mem_before) / 1024 / 1024
        avg_latency = statistics.mean([r["mean_ms"] for r in results])
        total_ops = sum(tc["iterations"] for tc in test_cases)
        validation_accuracy = 1.0 - (validation_failures / total_ops)

        # Success criteria: <100ms latency, >99.5% validation, <10MB memory
        meets_latency = avg_latency < 100
        meets_validation = validation_accuracy > 0.995
        meets_memory = mem_delta_mb < 10
        overall_pass = meets_latency and meets_validation and meets_memory

        failure_type = None
        if not overall_pass:
            if not meets_latency:
                failure_type = FailureType.TIMEOUT
            elif not meets_validation:
                failure_type = FailureType.ERROR
            else:
                failure_type = FailureType.ERROR

        return EvalResult(
            name=self.name,
            passed=overall_pass,
            score=max(
                0.0,
                min(
                    1.0,
                    (
                        validation_accuracy
                        + (1.0 - avg_latency / 1000)
                        + (1.0 if meets_memory else 0.0)
                    )
                    / 3,
                ),
            ),
            duration=0.0,
            expected="<100ms latency, >99.5% validation, <10MB memory",
            actual=f"Latency: {avg_latency:.1f}ms, Validation: {validation_accuracy:.1%}, Memory: {mem_delta_mb:.1f}MB",
            failure_type=failure_type,
            metadata={
                "avg_latency_ms": avg_latency,
                "validation_accuracy": validation_accuracy,
                "memory_delta_mb": mem_delta_mb,
                "individual_results": results,
                "meets_latency": meets_latency,
                "meets_validation": meets_validation,
                "meets_memory": meets_memory,
            },
        )

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
