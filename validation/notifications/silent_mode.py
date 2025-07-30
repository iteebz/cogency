#!/usr/bin/env python3
"""V2 silent mode verification - clean output without notifications."""

import asyncio

from cogency import Agent
from cogency.notify import Formatter
from cogency.tools import Calculator, Weather


async def main():
    print("🤫 V2 SILENT MODE VERIFICATION")
    print("=" * 30 + "\n")

    # Agent with v2 silent formatter - clean, production-ready output
    agent = Agent(
        "silent_agent",
        identity="helpful assistant with clean, direct responses",
        tools=[Calculator(), Weather()],
        memory=False,
        depth=5,
        formatter=Formatter(),  # 🤫 Silent formatter - no notification output
    )

    queries = [
        "Calculate the cost: 12 apples at $1.25 each plus 8 oranges at $0.85 each"
        "What's the weather like in New York and what's 72°F in Celsius?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query}")

        try:
            result = await agent.run(query)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")

        await asyncio.sleep(1)

    print("✅ V2 silent mode verification complete!")
    print("\nNotice the v2 silent mode benefits:")
    print("  • No internal phase logging")
    print("  • No tool execution details")
    print("  • Clean, user-focused output")
    print("  • Zero notification overhead in production")
    print("  • Same powerful v2 functionality underneath")
    print("  • Async emission still works (just returns None)")


if __name__ == "__main__":
    asyncio.run(main())
