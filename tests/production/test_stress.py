#!/usr/bin/env python3
"""Brutal production stress testing for Cogency framework."""

import asyncio
import time
import tracemalloc
import psutil
import statistics
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
from cogency import Agent


class ProductionStressTester:
    """No-bullshit production stress testing."""
    
    def __init__(self):
        self.results = []
        self.memory_snapshots = []
        self.process = psutil.Process()
    
    async def run_brutal_test(self):
        """Run comprehensive production stress tests."""
        print("🔥 BRUTAL PRODUCTION STRESS TEST")
        print("=" * 50)
        
        # Start memory tracking
        tracemalloc.start()
        initial_memory = self.process.memory_info()
        
        tests = [
            ("Single Agent Performance", self.test_single_agent_performance),
            ("Concurrent Load Test", self.test_concurrent_load),
            ("Memory Leak Detection", self.test_memory_leaks),
            ("Error Recovery Under Load", self.test_error_recovery),
            ("Long Running Session", self.test_long_running_session)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 {test_name}")
            print("-" * 30)
            
            start_time = time.time()
            start_memory = self.process.memory_info()
            
            try:
                await test_func()
                print(f"✅ {test_name} PASSED")
            except Exception as e:
                print(f"❌ {test_name} FAILED: {e}")
                traceback.print_exc()
            
            end_time = time.time()
            end_memory = self.process.memory_info()
            
            self.results.append({
                "test": test_name,
                "duration": end_time - start_time,
                "memory_delta": end_memory.rss - start_memory.rss,
                "memory_current": end_memory.rss / 1024 / 1024  # MB
            })
        
        # Final memory snapshot
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        
        final_memory = self.process.memory_info()
        print(f"\n📊 PRODUCTION READINESS REPORT")
        print("=" * 50)
        print(f"Initial Memory: {initial_memory.rss / 1024 / 1024:.1f} MB")
        print(f"Final Memory: {final_memory.rss / 1024 / 1024:.1f} MB")
        print(f"Memory Delta: {(final_memory.rss - initial_memory.rss) / 1024 / 1024:.1f} MB")
        print(f"Peak Traced Memory: {peak / 1024 / 1024:.1f} MB")
        
        self.print_detailed_results()
    
    async def test_single_agent_performance(self):
        """Test single agent performance baseline."""
        agent = Agent("stress_test")
        
        response_times = []
        queries = [
            "What is Python?",
            "Explain machine learning in detail with examples and use cases",
            "Simple math: 2+2",
            "Complex analysis: Compare different sorting algorithms and their trade-offs",
            "Quick question: What time is it?"
        ]
        
        for query in queries:
            start = time.time()
            result = await agent.run(query)
            end = time.time()
            
            response_time = end - start
            response_times.append(response_time)
            
            print(f"  Query: '{query[:30]}...' - {response_time:.2f}s")
            assert len(result) > 0, "Empty response"
        
        avg_time = statistics.mean(response_times)
        max_time = max(response_times)
        
        print(f"  Average Response Time: {avg_time:.2f}s")
        print(f"  Max Response Time: {max_time:.2f}s")
        
        # Production thresholds
        assert avg_time < 10.0, f"Average response time too slow: {avg_time:.2f}s"
        assert max_time < 30.0, f"Max response time too slow: {max_time:.2f}s"
    
    async def test_concurrent_load(self):
        """Test concurrent load handling."""
        concurrent_agents = 5
        queries_per_agent = 3
        
        async def agent_worker(agent_id: int):
            agent = Agent(f"concurrent_{agent_id}")
            results = []
            
            for i in range(queries_per_agent):
                start = time.time()
                result = await agent.run(f"Agent {agent_id} query {i}: What is {i * 2}?")
                end = time.time()
                
                results.append({
                    "agent_id": agent_id,
                    "query_id": i,
                    "response_time": end - start,
                    "result_length": len(result)
                })
            
            return results
        
        # Run concurrent agents
        start_total = time.time()
        tasks = [agent_worker(i) for i in range(concurrent_agents)]
        all_results = await asyncio.gather(*tasks)
        end_total = time.time()
        
        # Analyze results
        total_queries = concurrent_agents * queries_per_agent
        total_time = end_total - start_total
        throughput = total_queries / total_time
        
        all_response_times = []
        for agent_results in all_results:
            all_response_times.extend([r["response_time"] for r in agent_results])
        
        avg_response = statistics.mean(all_response_times)
        
        print(f"  Concurrent Agents: {concurrent_agents}")
        print(f"  Total Queries: {total_queries}")
        print(f"  Total Time: {total_time:.2f}s")
        print(f"  Throughput: {throughput:.2f} queries/sec")
        print(f"  Avg Response Time: {avg_response:.2f}s")
        
        # Production thresholds
        assert throughput > 0.1, f"Throughput too low: {throughput:.2f} queries/sec"
        assert avg_response < 15.0, f"Concurrent response time too slow: {avg_response:.2f}s"
    
    async def test_memory_leaks(self):
        """Test for memory leaks under repeated usage."""
        agent = Agent("memory_test")
        
        memory_samples = []
        iterations = 20
        
        for i in range(iterations):
            # Take memory snapshot
            current_memory = self.process.memory_info().rss / 1024 / 1024
            memory_samples.append(current_memory)
            
            # Run agent
            await agent.run(f"Memory test iteration {i}: explain recursion")
            
            # Force garbage collection
            import gc
            gc.collect()
            
            if i % 5 == 0:
                print(f"  Iteration {i}: {current_memory:.1f} MB")
        
        # Analyze memory growth
        initial_memory = memory_samples[0]
        final_memory = memory_samples[-1]
        memory_growth = final_memory - initial_memory
        
        # Calculate trend
        if len(memory_samples) > 1:
            x = list(range(len(memory_samples)))
            y = memory_samples
            # Simple linear regression slope
            n = len(x)
            slope = (n * sum(x[i] * y[i] for i in range(n)) - sum(x) * sum(y)) / (n * sum(x[i]**2 for i in range(n)) - sum(x)**2)
        else:
            slope = 0
        
        print(f"  Initial Memory: {initial_memory:.1f} MB")
        print(f"  Final Memory: {final_memory:.1f} MB")
        print(f"  Memory Growth: {memory_growth:.1f} MB")
        print(f"  Growth Trend: {slope:.3f} MB/iteration")
        
        # Production thresholds
        assert memory_growth < 50.0, f"Memory leak detected: {memory_growth:.1f} MB growth"
        assert abs(slope) < 1.0, f"Memory trend concerning: {slope:.3f} MB/iteration"
    
    async def test_error_recovery(self):
        """Test error recovery under load."""
        # Test with invalid queries and network issues
        agent = Agent("error_test")
        
        error_scenarios = [
            "",  # Empty query
            "x" * 10000,  # Extremely long query
            "Invalid unicode: \x00\x01\x02",  # Invalid characters
            "Normal query after errors"  # Recovery test
        ]
        
        successful_recoveries = 0
        
        for i, query in enumerate(error_scenarios):
            try:
                result = await agent.run(query)
                if len(result) > 0:
                    successful_recoveries += 1
                    print(f"  Scenario {i}: ✅ Recovered")
                else:
                    print(f"  Scenario {i}: ⚠️ Empty response")
            except Exception as e:
                print(f"  Scenario {i}: ❌ Error: {type(e).__name__}")
        
        recovery_rate = successful_recoveries / len(error_scenarios)
        print(f"  Recovery Rate: {recovery_rate:.1%}")
        
        # Should handle at least basic recovery
        assert recovery_rate >= 0.5, f"Poor error recovery: {recovery_rate:.1%}"
    
    async def test_long_running_session(self):
        """Test long-running session stability."""
        agent = Agent("endurance_test")
        
        session_queries = [
            "Start session: What is Python?",
            "Continue: Explain variables",
            "More detail: Show code examples",
            "New topic: What about functions?",
            "Wrap up: Summarize our discussion"
        ]
        
        session_start = time.time()
        total_response_length = 0
        
        for i, query in enumerate(session_queries):
            start = time.time()
            result = await agent.run(query)
            end = time.time()
            
            total_response_length += len(result)
            print(f"  Query {i+1}: {end - start:.2f}s, {len(result)} chars")
            
            # Simulate realistic pause between queries
            await asyncio.sleep(0.1)
        
        session_end = time.time()
        session_duration = session_end - session_start
        
        print(f"  Session Duration: {session_duration:.2f}s")
        print(f"  Total Response Length: {total_response_length} chars")
        
        # Basic session consistency
        assert session_duration < 60.0, f"Session too slow: {session_duration:.2f}s"
        assert total_response_length > 0, "No responses generated"
    
    def print_detailed_results(self):
        """Print detailed performance analysis."""
        print("\n📈 DETAILED PERFORMANCE ANALYSIS")
        print("-" * 50)
        
        for result in self.results:
            print(f"Test: {result['test']}")
            print(f"  Duration: {result['duration']:.2f}s")
            print(f"  Memory Delta: {result['memory_delta'] / 1024 / 1024:.1f} MB")
            print(f"  Current Memory: {result['memory_current']:.1f} MB")
            print()


async def main():
    """Run production stress tests."""
    tester = ProductionStressTester()
    await tester.run_brutal_test()


if __name__ == "__main__":
    asyncio.run(main())