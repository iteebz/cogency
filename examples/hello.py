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
    
    # Personality injection - DX couldn't be easier
    print("\n🎭 Now with personality...")
    pirate = Agent("pirate", personality="a friendly pirate who loves coding and says 'ahoy' a lot")
    await pirate.run_streaming("Tell me about Cogency!")
    print("🏴‍☠️ Ahoy!")

if __name__ == "__main__":
    asyncio.run(main())