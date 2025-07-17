#!/usr/bin/env python3
"""Basic agent with weather tool."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("weather_assistant")
    await agent.run_streaming("What's the weather in San Francisco?")

if __name__ == "__main__":
    asyncio.run(main())