#!/usr/bin/env python3
"""Performance profiling - timing analysis for Claude debugging."""

import asyncio
import time

from cogency import Agent
from cogency.context.assembly import build_context


async def main():
    """Profile key operations."""
    print("=== PERFORMANCE PROFILING ===")

    # Profile context assembly
    start = time.perf_counter()
    context = await build_context(user_id="default", query="test performance query", iteration=1)
    context_time = (time.perf_counter() - start) * 1000
    print(f"Context assembly: {context_time:.1f}ms ({len(context)} chars)")

    # Profile Agent creation
    start = time.perf_counter()
    agent = Agent("assistant")
    agent_time = (time.perf_counter() - start) * 1000
    print(f"Agent creation: {agent_time:.1f}ms")

    # Profile simple execution
    print("\nRunning execution timing test...")
    start = time.perf_counter()
    response = await agent.run_async("What is the capital of France?")
    exec_time = (time.perf_counter() - start) * 1000
    print(f"Simple execution: {exec_time:.1f}ms ({len(response)} chars)")

    # Memory usage estimation

    total_size = len(context) + len(response)
    print(f"\nMemory footprint estimate: {total_size} chars (~{total_size/1024:.1f}KB)")


if __name__ == "__main__":
    asyncio.run(main())
