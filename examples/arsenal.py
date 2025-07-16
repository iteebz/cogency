#!/usr/bin/env python3
"""ADVANCED CHAINING - Multi-step problem solving with tool dependencies."""
import asyncio
import sys
from cogency import Agent

async def main():
    agent = Agent("cogency")

    print("Available Tools:")
    for tool in agent.tools:
        print(f"- {tool.name}")
    print("=" * 50)

    if len(sys.argv) < 2:
        print("Usage: poetry run python examples/arsenal.py \"your query\"")
        sys.exit(1)
    
    query = sys.argv[1]
    print(f"Query: {query}")
    
    await agent.run_streaming(query, mode="summary")

if __name__ == "__main__":
    asyncio.run(main())