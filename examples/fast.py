#!/usr/bin/env python3
"""Fast thinking agent - simple code execution verification with fast thinking."""

import asyncio

from cogency import Agent
from cogency.tools import Code


async def main():
    print("⚡ FAST THINKING AGENT")
    print("=" * 30 + "\n")

    # Fast thinking agent with code tool for verification
    agent = Agent(
        "fast_thinker",
        identity="expert mathematician who thinks quickly and verifies calculations",
        tools=[Code()],
        memory=False,
        depth=5,  # Keep it quick
        mode="fast",
    )

    # Math problem that requires fast thinking and verification
    query = """I need to quickly solve this math problem and verify my thinking:

    A store sells apples for $1.25 each and oranges for $0.85 each. 
    If I buy 12 apples and 8 oranges, what's the total cost?
    
    Please think through this quickly and use the code tool to verify your mental math."""

    print(f"👤 {query}...\n")
    async for chunk in agent.stream(query):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
