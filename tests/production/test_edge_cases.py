#!/usr/bin/env python3
"""Brutal edge case testing for production hardening."""

import asyncio
import time
import logging
from cogency import Agent
from cogency.core.resilience import RateLimitedError, CircuitOpenError
from cogency.core.metrics import get_metrics


async def test_edge_cases():
    """Test brutal edge cases that break production systems."""
    print("💀 BRUTAL EDGE CASE TESTING")
    print("=" * 50)
    
    agent = Agent("edge_case_test")
    
    edge_cases = [
        # Empty/minimal
        ("", "empty_query"),
        ("x", "single_char"),
        
        # Extremely long
        ("x" * 5000, "extremely_long_query"),
        
        # Special characters
        ("🚀💀🔥" * 100, "emoji_spam"),
        ("What\x00is\x01this\x02", "null_bytes"),
        
        # Complex queries
        ("Analyze the performance implications of different machine learning frameworks and compare their trade-offs in detail", "complex_analysis"),
        
        # Rapid fire
        ("Quick " + str(i) for i in range(10)),
    ]
    
    results = []
    
    print("\n🧪 Testing Edge Cases")
    print("-" * 30)
    
    for i, (query, case_type) in enumerate(edge_cases[:-1]):  # Skip rapid fire for now
        print(f"  Case {i+1} ({case_type}): ", end="")
        
        start = time.time()
        try:
            result = await agent.run(query)
            end = time.time()
            
            status = "✅ SUCCESS"
            error = None
            response_length = len(result)
            duration = end - start
            
        except RateLimitedError:
            status = "⚠️ RATE_LIMITED"
            error = "rate_limited"
            response_length = 0
            duration = time.time() - start
            
        except CircuitOpenError:
            status = "🔴 CIRCUIT_OPEN"
            error = "circuit_open"
            response_length = 0
            duration = time.time() - start
            
        except Exception as e:
            status = f"❌ {type(e).__name__}"
            error = str(e)
            response_length = 0
            duration = time.time() - start
        
        results.append({
            "case": case_type,
            "query_length": len(query),
            "status": status,
            "error": error,
            "response_length": response_length,
            "duration": duration
        })
        
        print(f"{status} ({duration:.2f}s)")
        
        # Brief pause to avoid overwhelming
        await asyncio.sleep(0.5)
    
    # Rapid fire test
    print("\n  Rapid Fire Test: ", end="")
    rapid_start = time.time()
    rapid_successes = 0
    rapid_failures = 0
    
    for i in range(5):  # Reduced from 10 to be more reasonable
        try:
            await agent.run(f"Rapid {i}")
            rapid_successes += 1
        except (RateLimitedError, CircuitOpenError):
            rapid_failures += 1
        except Exception:
            rapid_failures += 1
    
    rapid_duration = time.time() - rapid_start
    print(f"✅ {rapid_successes}/{rapid_successes + rapid_failures} in {rapid_duration:.2f}s")
    
    # Results analysis
    print("\n📊 EDGE CASE ANALYSIS")
    print("-" * 30)
    
    success_rate = sum(1 for r in results if "SUCCESS" in r["status"]) / len(results)
    avg_response_time = sum(r["duration"] for r in results if r["duration"]) / len(results)
    
    print(f"  Overall Success Rate: {success_rate:.1%}")
    print(f"  Average Response Time: {avg_response_time:.2f}s")
    
    # Group by status
    status_groups = {}
    for result in results:
        status = result["status"].split()[0]  # Get just the emoji/status part
        if status not in status_groups:
            status_groups[status] = []
        status_groups[status].append(result)
    
    for status, group in status_groups.items():
        print(f"  {status}: {len(group)} cases")
        if group:
            avg_time = sum(r["duration"] for r in group) / len(group)
            print(f"    Average time: {avg_time:.2f}s")
    
    # Resilience metrics
    metrics = get_metrics()
    summaries = metrics.get_all_summaries()
    
    print("\n🛡️ RESILIENCE METRICS")
    print("-" * 30)
    
    for summary in summaries:
        if "error" in summary.name or "rate_limited" in summary.name or "circuit" in summary.name:
            print(f"  {summary.name}: {summary.count} occurrences")
    
    print("\n💀 EDGE CASE TESTING COMPLETE")
    print(f"System survived {len(results) + 5} brutal tests with {success_rate:.1%} success rate")


async def test_memory_stress():
    """Test memory behavior under stress."""
    print("\n🧠 MEMORY STRESS TEST")
    print("-" * 30)
    
    import psutil
    import gc
    
    process = psutil.Process()
    initial_memory = process.memory_info().rss / 1024 / 1024
    
    print(f"  Initial Memory: {initial_memory:.1f} MB")
    
    # Create multiple agents to test memory usage
    agents = []
    for i in range(3):
        agent = Agent(f"memory_test_{i}")
        agents.append(agent)
        
        # Run a query on each
        try:
            await agent.run(f"Memory test {i}")
        except Exception:
            pass  # Ignore errors, we're testing memory
    
    current_memory = process.memory_info().rss / 1024 / 1024
    print(f"  After 3 agents: {current_memory:.1f} MB (+{current_memory - initial_memory:.1f} MB)")
    
    # Force garbage collection
    del agents
    gc.collect()
    
    final_memory = process.memory_info().rss / 1024 / 1024
    print(f"  After cleanup: {final_memory:.1f} MB")
    
    memory_growth = final_memory - initial_memory
    if memory_growth < 20:  # Less than 20MB growth is reasonable
        print(f"  ✅ Memory usage acceptable: +{memory_growth:.1f} MB")
    else:
        print(f"  ⚠️ Memory growth concerning: +{memory_growth:.1f} MB")


async def main():
    """Run all edge case tests."""
    # Reduce logging noise
    logging.getLogger("metrics").setLevel(logging.WARNING)
    
    await test_edge_cases()
    await test_memory_stress()


if __name__ == "__main__":
    asyncio.run(main())