"""Cogency v2.0.0 - Canonical Reference Example"""

import asyncio
import os

from cogency import Agent, profile, BASIC_TOOLS


async def main():
    # Set API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable")
        return

    # Simple usage - zero ceremony
    agent = Agent()
    response = await agent("What is 2+2?")
    print(f"Simple: {response}")

    # Configured usage - set once, use many
    dev_agent = Agent(model="gpt-4o-mini", tools=BASIC_TOOLS, verbose=True)
    response = await dev_agent("Calculate 10 factorial")
    print(f"Configured: {response}")

    # Multi-provider support
    if os.getenv("ANTHROPIC_API_KEY"):
        claude_agent = Agent(model="claude-sonnet-4-20250514")
        response = await claude_agent("What is the capital of France?")
        print(f"Claude 4: {response}")

    # With user profile
    profile("alice", name="Alice", preferences=["Python"], context="Developer")
    response = await agent("Recommend a Python library", user_id="alice")
    print(f"Profile: {response}")


if __name__ == "__main__":
    asyncio.run(main())
