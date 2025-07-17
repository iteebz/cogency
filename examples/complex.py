#!/usr/bin/env python3
"""Multi-step reasoning with tool chaining."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("travel_planner")
    
    scenario = """
    I'm planning a trip to London:
    1. What's the weather there?
    2. What time is it now?
    3. Flight costs $1,200, hotel is $180/night for 3 nights - total cost?
    """
    
    await agent.run_streaming(scenario)

if __name__ == "__main__":
    asyncio.run(main())