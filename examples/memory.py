#!/usr/bin/env python3
"""Memory example - save and recall information."""

import asyncio

from cogency import Agent
from cogency.utils.cli import trace_args


async def main():
    print("🧠 MEMORY DEMO")
    print("=" * 20)

    # Create agent with memory
    agent = Agent("assistant", memory=True, trace=trace_args())

    # Teach the agent
    query_1 = "My name is Alex, I'm a Python developer working on a fintech app"
    print(f"👤 {query_1}\n")
    async for chunk in agent.stream(query_1):
        print(chunk, end="", flush=True)

    # Test recall
    query_2 = "What do you know about me?"
    print(f"\n👤 {query_2}\n")
    async for chunk in agent.stream(query_2):
        print(chunk, end="", flush=True)

    # Apply memory
    query_3 = "What database should I use for my project?"
    print(f"\n👤 {query_3}\n")
    async for chunk in agent.stream(query_3):
        print(chunk, end="", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
