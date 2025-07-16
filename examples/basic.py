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
    
    # Show beautiful streaming by default
    print("🔄 ReAct Reasoning:")
    async for chunk in agent.stream(query, mode=mode):
        print(chunk, end="", flush=True)
    
    print("\n✅ Complete!")

if __name__ == "__main__":
    asyncio.run(main())