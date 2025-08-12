#!/usr/bin/env python3
"""Persistent Memory - Context that spans conversations."""

import asyncio

from cogency import Agent


async def session_1():
    """First conversation - establish context."""
    print("SESSION 1: Setting Context")
    print("=" * 40)

    agent = Agent("assistant", memory=True)

    await agent.run_async("""
    I'm the CTO of a fintech startup building a mobile banking app.
    Our stack is React Native, Node.js, PostgreSQL, and we're deployed on AWS.
    We have 50K users and are processing $2M in transactions monthly.
    My biggest concerns are security, scalability, and regulatory compliance.
    Remember all of this for future conversations.
    """)

    print("Context established ✓")


async def session_2():
    """Second conversation - test memory recall."""
    print("\nSESSION 2: Memory Recall")
    print("=" * 40)

    # Same user_id to access stored memory
    agent = Agent("assistant", memory=True)

    response = await agent.run_async("""
    We're seeing 15% latency increase during peak hours.
    What architectural changes should we prioritize?
    """)

    print(
        "Response considers our context:",
        "✓" if any(term in response for term in ["fintech", "50K", "banking", "AWS"]) else "✗",
    )


async def main():
    await session_1()
    await session_2()


if __name__ == "__main__":
    asyncio.run(main())
