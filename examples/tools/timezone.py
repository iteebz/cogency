#!/usr/bin/env python3
"""Timezone tool isolation test."""
import asyncio
from cogency import Agent, TimezoneTool

async def main():
    print("🕐 Testing TimezoneTool...")
    agent = Agent("time", tools=[TimezoneTool()])
    result = await agent.run("What time is it in Tokyo?")
    result_str = str(result).lower()
    has_time = any(word in result_str for word in ["time", "timezone", "tokyo", ":"])
    assert has_time, f"No time info: {result}"

if __name__ == "__main__":
    asyncio.run(main())