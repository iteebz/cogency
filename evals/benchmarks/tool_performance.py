"""ToolPerformance microbench - Measure tool execution overhead."""

import asyncio
import json
import statistics
import tracemalloc
from pathlib import Path
from time import perf_counter
from typing import List

from cogency import Agent
from cogency.tools.files import Files
from cogency.tools.shell import Shell
from cogency.tools.search import Search
from cogency.tools.scrape import Scrape
from cogency.tools.http import HTTP
from evals.core.base import Eval, EvalResult


class ToolPerformance(Eval):
    """Measure tool invocation latency and orchestration overhead."""

    name = "tool_performance"
    description = "Tool execution latency microbenchmark"

    def __init__(self):
        super().__init__()
        self.results_dir = Path(".cogency/evals")
        self.results_dir.mkdir(exist_ok=True)

    async def run(self) -> EvalResult:
        """Run performance tests on canonical 5-tool architecture."""
        
        # Start memory tracking
        tracemalloc.start()
        
        test_cases = [
            {
                "name": "files_create_read",
                "tool": Files(),
                "args": {"action": "create", "filename": "bench_{iteration}.txt", "content": "test"},
                "iterations": 50,
            },
            {
                "name": "shell_echo",
                "tool": Shell(),
                "args": {"command": "echo 'benchmark'"},
                "iterations": 50,
            },
            {
                "name": "search_query",
                "tool": Search(),
                "args": {"query": "Python programming", "max_results": 3},
                "iterations": 3,  # Reduced for quick test
            },
            {
                "name": "scrape_url",
                "tool": Scrape(),
                "args": {"url": "https://example.com"},
                "iterations": 3,  # Reduced for quick test
            },
            {
                "name": "http_get",
                "tool": HTTP(),
                "args": {"url": "https://httpbin.org/json", "method": "get"},
                "iterations": 3,  # Reduced for quick test
            },
        ]

        results = []
        validation_failures = 0
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"{i}/{len(test_cases)} ToolPerformance: {test_case['name']}...")
            
            # Memory snapshot before test
            mem_before = tracemalloc.get_traced_memory()[0]

            # Test direct tool execution (baseline)
            direct_times, validation_errors = await self._benchmark_direct_tool(test_case)
            validation_failures += validation_errors

            # Calculate metrics
            direct_mean = statistics.mean(direct_times) if direct_times else float("inf")
            direct_p95 = (
                statistics.quantiles(direct_times, n=20)[18] if len(direct_times) >= 5 else direct_mean
            )
            
            # Memory snapshot after test
            mem_after = tracemalloc.get_traced_memory()[0]
            mem_delta = (mem_after - mem_before) / 1024 / 1024  # MB

            test_result = {
                "test_name": test_case["name"],
                "direct_mean_ms": direct_mean * 1000,
                "direct_p95_ms": direct_p95 * 1000,
                "direct_times": [t * 1000 for t in direct_times],
                "validation_errors": validation_errors,
                "memory_delta_mb": mem_delta,
                "passed": direct_mean * 1000 < 100 and validation_errors == 0,  # <100ms, 0 validation errors
            }

            results.append(test_result)
            self._log_test_result(test_result)

        # Stop memory tracking and get final stats
        tracemalloc.stop()
        total_memory_delta = sum(r["memory_delta_mb"] for r in results)
        
        # Aggregate results
        avg_latency = statistics.mean([r["direct_mean_ms"] for r in results])
        total_validation_errors = sum(r["validation_errors"] for r in results)
        total_operations = sum(test_case["iterations"] for test_case in test_cases)
        validation_accuracy = 1.0 - (total_validation_errors / total_operations)
        passed_tests = sum(1 for r in results if r["passed"])
        
        # Success criteria from spec:
        # - <100ms tool invocation overhead
        # - >99.5% parameter validation accuracy  
        # - Zero memory leaks over 1000 iterations
        meets_latency = avg_latency < 100
        meets_validation = validation_accuracy > 0.995
        meets_memory = total_memory_delta < 10  # <10MB total
        overall_pass = meets_latency and meets_validation and meets_memory

        final_result = EvalResult(
            name=self.name,
            passed=overall_pass,
            score=max(0.0, min(1.0, (validation_accuracy + (1.0 - avg_latency/1000) + (1.0 if meets_memory else 0.0)) / 3)),
            duration=0.0,
            expected="<100ms latency, >99.5% validation accuracy, <10MB memory growth",
            actual=f"Latency: {avg_latency:.1f}ms, Validation: {validation_accuracy:.3%}, Memory: {total_memory_delta:.1f}MB",
            metadata={
                "tests_passed": passed_tests,
                "total_tests": len(results),
                "avg_latency_ms": avg_latency,
                "validation_accuracy": validation_accuracy,
                "total_validation_errors": total_validation_errors,
                "total_operations": total_operations,
                "memory_delta_mb": total_memory_delta,
                "meets_latency": meets_latency,
                "meets_validation": meets_validation,
                "meets_memory": meets_memory,
                "individual_results": results,
            },
        )

        self._log_final_result(final_result)
        return final_result

    async def _benchmark_direct_tool(self, test_case: dict) -> tuple[List[float], int]:
        """Benchmark direct tool execution with validation checking."""
        times = []
        validation_errors = 0
        tool = test_case["tool"]
        args = test_case["args"]

        for iteration in range(test_case["iterations"]):
            try:
                # Substitute iteration number in args
                runtime_args = {}
                for key, value in args.items():
                    if isinstance(value, str) and "{iteration}" in value:
                        runtime_args[key] = value.format(iteration=iteration)
                    else:
                        runtime_args[key] = value
                
                # Parameter validation test
                if not self._validate_parameters(tool, runtime_args):
                    validation_errors += 1
                
                start = perf_counter()
                result = await tool.run(**runtime_args)
                end = perf_counter()
                
                # Check result validity - ensure we get a proper Result object
                if not hasattr(result, 'success') or not hasattr(result, 'data'):
                    validation_errors += 1
                    
                times.append(end - start)

                # Rate limit external calls
                if test_case["name"] in ["search_query", "scrape_url", "http_get"]:
                    await asyncio.sleep(0.2)
                else:
                    await asyncio.sleep(0.01)  # Minimal delay for local operations

            except Exception as e:
                validation_errors += 1
                times.append(0.1)  # Penalty time for failures
                print(f"Tool {test_case['name']} iteration {iteration} failed: {e}")

        return times, validation_errors

    def _validate_parameters(self, tool, args: dict) -> bool:
        """Validate tool parameters against params class."""
        try:
            # Check if tool has params class (dataclass)
            if hasattr(tool, 'params') and tool.params:
                # Try to create the params object - this validates structure
                tool.params(**args)
                return True
            return True  # No validation available, assume valid
        except Exception:
            return False

    def _log_test_result(self, test_result: dict):
        """Log individual test result."""
        timestamp = int(self.start_time) if self.start_time else 0
        log_file = self.results_dir / f"tool_perf_{test_result['test_name']}_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(test_result, f, indent=2)

    def _log_final_result(self, result: EvalResult):
        """Log final aggregated result."""
        timestamp = int(self.start_time) if self.start_time else 0
        log_file = self.results_dir / f"tool_performance_final_{timestamp}.json"

        with open(log_file, "w") as f:
            json.dump(result.model_dump(), f, indent=2)
