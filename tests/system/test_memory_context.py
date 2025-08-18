"""System Test: Memory Context Capability Baseline"""

import asyncio
import os

from cogency import Agent, profile


async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable")
        return

    # Create user profile for context
    profile(
        "developer",
        name="Alex",
        preferences=["Python", "AI", "clean code"],
        context="Senior software engineer",
    )

    # Agent with user context
    agent = Agent(user_id="developer")
    result = await agent("Recommend a good Python library for data processing")

    print(f"Contextual response: {result}")
    print(f"Conversation: {result.conversation_id}")


if __name__ == "__main__":
    asyncio.run(main())
