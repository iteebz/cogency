#!/usr/bin/env python3
"""Custom tool in 10 lines - shows how stupidly easy it is."""
import asyncio
from cogency import Agent, WeatherTool

async def main():
    # That's it - use built-in tools or add your own
    agent = Agent("weather_assistant", tools=[WeatherTool()])
    result = await agent.run("What's the weather in San Francisco?")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())