#!/usr/bin/env python3
"""Sequential reasoning - Multi-step tool dependencies."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("research_assistant")
    
    # This demonstrates sequential tool usage where each step depends on the previous
    query = """I need to research Python's popularity:
    1. First, search for "Python programming language popularity 2024"
    2. Then calculate what percentage 45 million is of 200 million total developers
    3. Finally, create a summary file called 'python_research.txt' with the findings"""
    
    await agent.query(query)

if __name__ == "__main__":
    asyncio.run(main())