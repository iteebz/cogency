#!/usr/bin/env python3
"""Conversation history - Multi-turn dialogue with context."""
import asyncio
from cogency import Agent

async def main():
    agent = Agent("conversation_assistant")
    user_id = "demo_user"
    
    print("=== Turn 1: Initial question ===")
    await agent.query("What's 15% of 200?", user_id)
    
    print("\n=== Turn 2: Follow-up question ===")
    await agent.query("Now add 50 to that result", user_id)
    
    print("\n=== Turn 3: Context reference ===")
    await agent.query("What was my original number again?", user_id)

if __name__ == "__main__":
    asyncio.run(main())