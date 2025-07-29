#!/usr/bin/env python3
"""Basic weather tool verification - API integration test."""

import asyncio

from cogency import Agent
from cogency.tools import Weather


async def main():
    print("🌤️ WEATHER VERIFICATION")
    print("=" * 30 + "\n")

    # Simple agent with weather tool
    agent = Agent(
        "weather_tester",
        identity="helpful weather assistant providing current conditions",
        tools=[Weather()],
        memory=False,
        max_iterations=3,
        trace=False,  # Clean output
    )

    # Test weather queries
    queries = [
        "What's the weather in San Francisco?",
        "Tell me the current weather in London",
        "How's the weather in Tokyo right now?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"Test {i}: {query}")
        try:
            result = await agent.run(query)
            print(f"Result: {result}\n")
        except Exception as e:
            print(f"Error: {e}\n")
        await asyncio.sleep(1)  # Be nice to the API

    print("✅ Weather verification complete!")


if __name__ == "__main__":
    asyncio.run(main())
