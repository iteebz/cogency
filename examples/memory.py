#!/usr/bin/env python3
"""Memory tool isolation test - Smart memory behavior."""
import asyncio
from cogency import Agent, FSMemory

async def main():
    memory = FSMemory(memory_dir=".memory")
    agent = Agent("memory", memory=memory)
    
    async for chunk in agent.stream("I have ADHD and work as a software engineer in SF"):
        print(chunk, end="", flush=True)
    
    print("\n\n")
    async for chunk in agent.stream("What do you know about my work situation?"):
        print(chunk, end="", flush=True)

if __name__ == "__main__":
    asyncio.run(main())