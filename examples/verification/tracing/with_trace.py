#!/usr/bin/env python3
"""Tracing enabled verification - see internal phase execution."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator, Weather


async def main():
    print("🔍 TRACING ENABLED VERIFICATION")
    print("=" * 40 + "\n")

    # Agent with tracing enabled - shows internal phase execution
    agent = Agent(
        "traced_agent",
        identity="helpful assistant with visible internal reasoning",
        tools=[Calculator(), Weather()],
        memory=False,
        max_iterations=5,
        trace=True,  # 🔍 TRACING ON - see the magic happen
        verbose=True,
    )

    queries = [
        "Calculate the cost: 12 apples at $1.25 each plus 8 oranges at $0.85 each",
        "What's the weather like in New York and what's 72°F in Celsius?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'='*50}")
        print(f"TRACED QUERY {i}: {query}")
        print('='*50)
        
        try:
            result = await agent.run(query)
            print(f"\n🎯 FINAL RESULT: {result}")
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
        
        if i < len(queries):
            print("\n" + "⏳ Next query in 2 seconds..." + "\n")
            await asyncio.sleep(2)

    print(f"\n{'='*50}")
    print("✅ TRACING VERIFICATION COMPLETE!")
    print("Notice how you can see:")
    print("  • Phase transitions (preprocess → reason → act → respond)")
    print("  • Tool selection and execution")
    print("  • State updates between phases")
    print("  • Internal reasoning process")
    print(f"{'='*50}")


if __name__ == "__main__":
    asyncio.run(main())