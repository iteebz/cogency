"""Cogency v2.1.0 - Evolutionary Agent Example"""

import asyncio
import os

from cogency import BASIC_TOOLS, Agent, profile


async def main():
    # Set API key
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable")
        return

    # Pure agent - zero ceremony
    agent = Agent()
    result = await agent("What is 2+2?")
    print(f"Pure: {result}")  # AgentResult prints as response via __str__

    # With user profile - enhanced context
    profile("alice", name="Alice", preferences=["Python"], context="Developer")
    alice_agent = Agent(user_id="alice")
    result = await alice_agent("Recommend a Python library")
    print(f"Profile: {result}")  # Backward compatible printing

    # Intelligent agent - tool-enabled reasoning
    intelligent = Agent(tools=BASIC_TOOLS)
    result = await intelligent("Create a Python file that calculates 10!")
    print(f"Intelligent: {result}")
    print(f"Conversation: {result.conversation_id}")  # Access conversation tracking


if __name__ == "__main__":
    asyncio.run(main())
