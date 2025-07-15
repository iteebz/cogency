#!/usr/bin/env python3
"""The simplest possible agent - 3 lines that blow minds."""
import asyncio
from cogency import Agent

async def main():
    # That's it. Auto-detects LLM from .env, just works.
    agent = Agent("assistant")
    result = await agent.stream("Hello! Tell me about yourself.")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())