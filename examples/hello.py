#!/usr/bin/env python3
"""The simplest possible agent - 3 lines that blow minds."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("assistant")
    await agent.run_streaming("Hello! Tell me about yourself.")

if __name__ == "__main__":
    asyncio.run(main())