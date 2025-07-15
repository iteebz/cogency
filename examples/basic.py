#!/usr/bin/env python3
"""Single tool in 4 lines - shows the magic."""
import asyncio
from cogency import Agent, WeatherTool

async def main():
    agent = Agent("weather_assistant", tools=[WeatherTool()])
    result = await agent.run("What's the weather in San Francisco?")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())