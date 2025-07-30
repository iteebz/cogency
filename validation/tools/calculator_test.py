#!/usr/bin/env python3
"""Basic calculator tool verification - clean and simple."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator


async def main():
    print("🧮 CALCULATOR VERIFICATION")
    print("=" * 30 + "\n")

    # Simple agent with just calculator
    agent = Agent(
        "calculator_tester",
        identity="mathematical assistant focused on accurate calculations",
        tools=[Calculator()],
        memory=False,
        depth=3,
        trace=True,  # Show first iteration deep mode
    )

    # Test basic arithmetic
    queries = [
        "What is 1250 + 850?" "Calculate (12 * 1.25) + (8 * 0.85)" "What's the square root of 64?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"Test {i}: {query}")
        result = await agent.run(query)
        print(f"Result: {result}\n")
        await asyncio.sleep(0.5)  # Brief pause for readability

    print("✅ Calculator verification complete!")


if __name__ == "__main__":
    asyncio.run(main())
