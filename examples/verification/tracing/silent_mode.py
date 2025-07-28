#!/usr/bin/env python3
"""Silent mode verification - clean output without tracing."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator, Weather


async def main():
    print("🤫 SILENT MODE VERIFICATION")
    print("=" * 30 + "\n")

    # Agent with tracing disabled - clean, production-ready output
    agent = Agent(
        "silent_agent", 
        identity="helpful assistant with clean, direct responses",
        tools=[Calculator(), Weather()],
        memory=False,
        max_iterations=5,
        trace=False,  # 🤫 NO TRACING - clean output only
        verbose=False,
    )

    queries = [
        "Calculate the cost: 12 apples at $1.25 each plus 8 oranges at $0.85 each",
        "What's the weather like in New York and what's 72°F in Celsius?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query}")
        
        try:
            result = await agent.run(query)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")
        
        await asyncio.sleep(1)

    print("✅ Silent mode verification complete!")
    print("\nNotice the difference:")
    print("  • No internal phase logging")
    print("  • No tool execution details")
    print("  • Clean, user-focused output") 
    print("  • Same powerful functionality underneath")


if __name__ == "__main__":
    asyncio.run(main())