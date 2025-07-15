#!/usr/bin/env python3
"""Test all three output modes."""
import asyncio
import sys
from cogency import Agent, WeatherTool

async def main():
    agent = Agent("weather_assistant", tools=[WeatherTool()])
    query = "What's the weather in San Francisco?"
    
    # Get mode from command line arg or default to summary
    mode = "summary"
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    print(f"🧪 Testing mode: {mode}")
    print(f"🤖 Query: \"{query}\"")
    print()
    
    result = await agent.run(query, mode=mode)
    print(f"\n📝 Final response: {result}")

if __name__ == "__main__":
    asyncio.run(main())