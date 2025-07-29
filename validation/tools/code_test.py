#!/usr/bin/env python3
"""Basic code execution tool verification - sandboxed execution."""

import asyncio

from cogency import Agent
from cogency.tools import Code


async def main():
    print("🚀 CODE EXECUTION VERIFICATION")
    print("=" * 30 + "\n")

    # Simple agent with code execution
    agent = Agent(
        "code_tester",
        identity="programming assistant that executes code safely",
        tools=[Code()],
        memory=False,
        max_iterations=3,
        trace=False,  # Clean output
    )

    # Test code execution
    queries = [
        "Run this Python code: print('Hello, Cogency!')",
        "Execute: result = [x**2 for x in range(5)]; print(result)",
        "Calculate fibonacci: def fib(n): return n if n <= 1 else fib(n-1) + fib(n-2); print([fib(i) for i in range(8)])",
    ]

    for i, query in enumerate(queries, 1):
        print(f"Test {i}: {query}")
        try:
            result = await agent.run(query)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")
        await asyncio.sleep(0.5)

    print("✅ Code execution verification complete!")


if __name__ == "__main__":
    asyncio.run(main())
