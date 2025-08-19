"""System Test: Memory Context Capability Baseline"""

import asyncio

from cogency import Agent
from cogency.context import memory


async def main():
    # Create user profile for context
    memory.update(
        "developer",
        {
            "name": "Alex",
            "preferences": ["Python", "AI", "clean code"],
            "context": "Senior software engineer",
        },
    )

    # Agent with user context
    agent = Agent()
    result = await agent("Recommend a good Python library for data processing", user_id="developer")

    print(f"Contextual response: {result}")
    print(f"Conversation: {result.conversation_id}")


if __name__ == "__main__":
    asyncio.run(main())
