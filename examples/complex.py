#!/usr/bin/env python3
"""Multi-step reasoning with tool chaining."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("travel_planner")
    
    async for chunk in agent.stream("I'm planning a trip to London: What's the weather there? What time is it now? Flight costs $1,200, hotel is $180/night for 3 nights - total cost?"):
        print(chunk, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())