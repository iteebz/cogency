#!/usr/bin/env python3
"""Basic single-tool usage - Beautiful DX showcase."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("weather_assistant")
    await agent.query("What's the weather in Tokyo?")

if __name__ == "__main__":
    asyncio.run(main())