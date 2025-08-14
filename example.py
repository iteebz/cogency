"""Cogency v2.0.0 - Canonical Reference Example"""

import asyncio
import os

from cogency import Agent, ReAct, profile


async def main():
    # Set API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable")
        return

    # Basic agent
    agent = Agent()
    response = await agent("What is 2+2?")
    print(f"Basic: {response}")

    # With user profile
    profile("alice", name="Alice", preferences=["Python"], context="Developer")
    response = await agent("Recommend a Python library", user_id="alice")
    print(f"Profile: {response}")

    # ReAct agent with tools
    react = ReAct(verbose=True)
    result = await react.solve("Create a Python file that calculates 10!")
    print(f"ReAct: {result['final_answer']}")


if __name__ == "__main__":
    asyncio.run(main())
