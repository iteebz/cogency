#!/usr/bin/env python3
"""Basic agent with weather tool."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("weather_assistant")
    
    async for chunk in agent.stream("What's the weather in San Francisco?"):
        print(chunk, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())