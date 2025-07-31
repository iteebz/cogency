#!/usr/bin/env python3
"""Debug agent behavior with Gemini"""

import asyncio

from cogency import Agent
from cogency.tools import Calculator


async def debug_agent():
    """Debug agent with different queries."""

    print("🔍 AGENT DEBUG TEST")
    print("=" * 30)

    agent = Agent(
        "debug_agent",
        identity="debug test agent",
        memory=False,
        depth=3,
        observe=True,
        notify=True,
        llm="gemini",
        tools=[Calculator()],
    )

    queries = ["What is 5 + 3?", "Calculate 10 * 2", "What's 100 divided by 4?"]

    for i, query in enumerate(queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 25)
        try:
            result = await agent.run(query)
            print(f"Response: {result}")
        except Exception as e:
            print(f"Error: {e}")

        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(debug_agent())
