#!/usr/bin/env python3
"""ADVANCED CHAINING - Multi-step problem solving with tool dependencies."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("cogency")
    
    async for chunk in agent.stream("Plan a 3-day Tokyo itinerary with weather considerations."):
        print(chunk, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())