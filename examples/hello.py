#!/usr/bin/env python3
"""The simplest possible agent - 3 lines that blow minds."""
import asyncio
from cogency import Agent

async def main():
    # That's it. Auto-detects LLM from .env, just works.
    agent = Agent("assistant")
    
    print("🤖 Hello from Cogency!")
    await agent.run_streaming("Hello! Tell me about yourself.")
    print("✨ Done!")

if __name__ == "__main__":
    asyncio.run(main())