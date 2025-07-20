#!/usr/bin/env python3
"""Interactive testing - Test any query from command line."""
import asyncio
import sys
from cogency import Agent

async def main():
    if len(sys.argv) < 2:
        print("Usage: python interactive.py 'Your query here'")
        print("Example: python interactive.py 'What is 2+2 and what time is it in Tokyo?'")
        return
    
    query = " ".join(sys.argv[1:])
    agent = Agent("interactive_assistant")
    
    await agent.query(query)

if __name__ == "__main__":
    asyncio.run(main())