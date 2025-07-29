#!/usr/bin/env python3
"""Fast thinking agent - simple calculator verification with fast thinking."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator
from cogency.utils import trace_args


async def main():
    print("⚡ FAST THINKING AGENT")
    print("=" * 30 + "\n")

    # Fast thinking agent with calculator for verification
    agent = Agent(
        "fast_thinker",
        identity="expert mathematician who thinks quickly and verifies calculations",
        tools=[Calculator()],
        memory=False,
        depth=5,  # Keep it quick
        mode="fast",
        debug=trace_args(),
    )

    # Math problem that requires fast thinking and verification
    query = """I need to quickly solve this math problem and verify my thinking:

    A store sells apples for $1.25 each and oranges for $0.85 each. 
    If I buy 12 apples and 8 oranges, what's the total cost?
    
    Please think through this quickly and use the calculator to verify your mental math."""

    print(f"👤 {query}...\n")
    async for chunk in agent.stream(query):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
