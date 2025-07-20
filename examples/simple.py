#!/usr/bin/env python3
"""Simplest possible example - No tools, just conversation."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("simple_assistant")
    await agent.query("Hello! What can you help me with?")

if __name__ == "__main__":
    asyncio.run(main())