#!/usr/bin/env python3
"""Weather tool isolation test."""
import asyncio
from cogency import Agent, WeatherTool

async def main():
    print("🌤️ Testing WeatherTool...")
    agent = Agent("weather", tools=[WeatherTool()])
    result = await agent.run("Weather in London")
    result_str = str(result).lower()
    has_weather = any(word in result_str for word in ["temperature", "°c", "°f", "weather"])
    assert has_weather, f"No weather info: {result}"

if __name__ == "__main__":
    asyncio.run(main())