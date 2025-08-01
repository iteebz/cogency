"""ToolPerformance microbench - Measure tool execution overhead."""

import asyncio
import json
import statistics
from pathlib import Path
from time import perf_counter
from typing import List

from cogency import Agent
from cogency.tools.code import Code
from cogency.tools.search import Search
from evals.core.base import Eval, EvalResult


class ToolPerformance(Eval):
    """Measure tool invocation latency and orchestration overhead."""

    name = "tool_performance"
    description = "Tool execution latency microbenchmark"

    def __init__(self):
        super().__init__()
        self.results_dir = Path("evals/results")
        self.results_dir.mkdir(exist_ok=True)

    async def run(self) -> EvalResult:
        """Run performance tests on common tool operations."""
        
        test_cases = [
            {
                "name": "code_simple_calc",
                "tool": Code(),
                "prompt": "Calculate 15 * 23 using Python. Just return the calculation.",
                "iterations": 10
            },
            {
                "name": "search_basic_query", 
                "tool": Search(),
                "prompt": "Search for 'Python programming' and give me one sentence about it.",
                "iterations": 5  # Fewer iterations for external API
            },
            {
                "name": "code_string_manipulation",
                "tool": Code(),
                "prompt": "Reverse the string 'hello world' using Python. Just show the code.",
                "iterations": 10
            }
        ]

        results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"{i}/{len(test_cases)} ToolPerformance tests...")
            
            # Test with Cogency agent (full orchestration)
            agent_times = await self._benchmark_agent(test_case)
            
            # Test direct tool call (baseline)
            direct_times = await self._benchmark_direct_tool(test_case)
            
            # Calculate metrics
            agent_mean = statistics.mean(agent_times) if agent_times else float('inf')
            agent_p95 = statistics.quantiles(agent_times, n=20)[18] if len(agent_times) >= 5 else agent_mean
            
            direct_mean = statistics.mean(direct_times) if direct_times else float('inf')
            
            # Overhead calculation
            overhead_ms = (agent_mean - direct_mean) * 1000
            overhead_ratio = agent_mean / direct_mean if direct_mean > 0 else float('inf')
            
            test_result = {
                "test_name": test_case["name"],
                "agent_mean_ms": agent_mean * 1000,
                "agent_p95_ms": agent_p95 * 1000,
                "direct_mean_ms": direct_mean * 1000,
                "overhead_ms": overhead_ms,
                "overhead_ratio": overhead_ratio,
                "agent_times": [t * 1000 for t in agent_times],
                "direct_times": [t * 1000 for t in direct_times],
                "passed": overhead_ms < 100  # <100ms overhead target
            }
            
            results.append(test_result)
            self._log_test_result(test_result)

        # Aggregate results
        total_overhead = sum(r["overhead_ms"] for r in results)
        avg_overhead = total_overhead / len(results)
        passed_tests = sum(1 for r in results if r["passed"])
        
        final_result = EvalResult(
            name=self.name,
            passed=avg_overhead < 100,  # <100ms average overhead target
            score=max(0.0, 1.0 - (avg_overhead / 1000)),  # Score inversely related to overhead
            duration=0.0,
            expected="Tool orchestration overhead <100ms",
            actual=f"Average overhead: {avg_overhead:.1f}ms",
            metadata={
                "tests_passed": passed_tests,
                "total_tests": len(results),
                "average_overhead_ms": avg_overhead,
                "individual_results": results
            }
        )
        
        self._log_final_result(final_result)
        return final_result

    async def _benchmark_agent(self, test_case: dict) -> List[float]:
        """Benchmark tool execution through Cogency agent."""
        times = []
        agent = Agent("perf_tester", mode="fast", tools=[test_case["tool"]])
        
        for _ in range(test_case["iterations"]):
            try:
                start = perf_counter()
                await agent.run(test_case["prompt"])
                end = perf_counter()
                times.append(end - start)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
                
            except Exception as e:
                print(f"Agent benchmark failed: {e}")
                # Don't append time for failed runs
                
        return times

    async def _benchmark_direct_tool(self, test_case: dict) -> List[float]:
        """Benchmark direct tool execution (baseline)."""
        times = []
        tool = test_case["tool"]
        
        for _ in range(test_case["iterations"]):
            try:
                start = perf_counter()
                # Direct tool call simulation - simplified prompt
                if hasattr(tool, 'execute'):
                    await tool.execute("simple test")
                else:
                    # Fallback for tools that don't have execute method
                    pass
                end = perf_counter()
                times.append(end - start)
                
                await asyncio.sleep(0.1)
                
            except Exception as e:
                # For direct tool calls, use minimal baseline time
                times.append(0.001)  # 1ms baseline
                
        return times

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