#!/usr/bin/env python3
"""Test production hardening features."""

import asyncio
import time
from cogency import Agent
from cogency.resilience import RateLimitedError, CircuitOpenError
from cogency.monitoring.metrics import get_metrics, MetricsReporter


async def test_production_hardening(mock_llm_response):
    """Test all production hardening features."""
    print("🔧 TESTING PRODUCTION HARDENING")
    print("=" * 50)
    
    agent = Agent("hardened_test", llm=mock_llm_response)
    metrics = get_metrics()
    reporter = MetricsReporter(metrics)
    
    # Test 1: Basic functionality with metrics
    print("\n🧪 Basic Agent with Metrics")
    print("-" * 30)
    
    start_time = time.time()
    try:
        result = await agent.run("What is 2+2?")
        print(f"✅ Basic query successful: {len(result)} chars in {time.time() - start_time:.2f}s")
    except Exception as e:
        print(f"❌ Basic query failed: {e}")
    
    # Test 2: Rate limiting behavior
    print("\n🧪 Rate Limiting Test")
    print("-" * 30)
    
    rapid_queries = []
    start_batch = time.time()
    
    for i in range(5):  # Try 5 rapid queries
        try:
            start = time.time()
            result = await agent.run(f"Quick test {i}")
            end = time.time()
            rapid_queries.append({
                "query": i,
                "success": True,
                "time": end - start,
                "result_length": len(result)
            })
            print(f"  Query {i}: ✅ {end - start:.2f}s")
        except RateLimitedError as e:
            rapid_queries.append({
                "query": i,
                "success": False,
                "error": "rate_limited",
                "time": None
            })
            print(f"  Query {i}: ⚠️ Rate limited")
        except Exception as e:
            rapid_queries.append({
                "query": i,
                "success": False,
                "error": str(e),
                "time": None
            })
            print(f"  Query {i}: ❌ Error: {type(e).__name__}")
    
    batch_time = time.time() - start_batch
    successful_queries = sum(1 for q in rapid_queries if q["success"])
    
    print(f"  Batch Results: {successful_queries}/{len(rapid_queries)} successful in {batch_time:.2f}s")
    
    # Test 3: Metrics collection
    print("\n🧪 Metrics Collection")
    print("-" * 30)
    
    summaries = metrics.get_all_summaries()
    if summaries:
        for summary in summaries:
            print(f"  {summary.name}: count={summary.count}, avg={summary.avg:.3f}s")
    else:
        print("  No metrics collected yet")
    
    # Test 4: Error recovery
    print("\n🧪 Error Recovery Test")
    print("-" * 30)
    
    try:
        # This should trigger rate limiting more aggressively
        for i in range(3):
            await agent.run("Recovery test")
            await asyncio.sleep(0.1)  # Brief pause
        print("  ✅ Error recovery working")
    except Exception as e:
        print(f"  ⚠️ Recovery test showed: {type(e).__name__}")
    
    # Final metrics report
    print("\n📊 FINAL METRICS REPORT")
    print("-" * 30)
    reporter.log_summary()
    
    # Export metrics
    import os
    diagnostics_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".diagnostics")
    os.makedirs(diagnostics_dir, exist_ok=True)
    output_path = os.path.join(diagnostics_dir, "production_metrics.json")
    reporter.export_json(output_path)
    print(f"  📁 Metrics exported to {output_path}")
    
    print("\n✅ PRODUCTION HARDENING TEST COMPLETE")


async def main():
    """Run production hardening tests."""
    await test_production_hardening()


if __name__ == "__main__":
    # Configure logging for better visibility
    import logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    asyncio.run(main())