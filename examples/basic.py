#!/usr/bin/env python3
"""Test all three output modes."""
import asyncio
import sys
from cogency import Agent
from cogency.tools import WeatherTool

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
    await agent.run_streaming(query, mode=mode)
    
    print("\n✅ Complete!")

if __name__ == "__main__":
    asyncio.run(main())