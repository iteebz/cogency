#!/usr/bin/env python3
"""Memory showcase - Intelligent save and recall."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("memory_assistant")
    
    print("=== Teaching the agent ===")
    await agent.query("My favorite programming language is Python and I work at OpenAI")
    
    print("\n=== Testing recall ===")
    await agent.query("What do you know about my preferences?")

if __name__ == "__main__":
    asyncio.run(main())