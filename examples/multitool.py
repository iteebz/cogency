#!/usr/bin/env python3
"""Multi-tool coordination - Parallel tool execution showcase."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("multi_tool_coordinator")
    
    # This demonstrates parallel tool execution and coordination
    query = """I'm planning a business trip to London. I need:
    1. Current weather in London
    2. Current time in London  
    3. Calculate the cost: flight $450 + hotel $120/night for 3 nights
    
    Give me a summary with all this information."""
    
    await agent.query(query)

if __name__ == "__main__":
    asyncio.run(main())