"""System Test: Basic Agent Capability Baseline"""

import asyncio
import os

from cogency import Agent


async def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("Set OPENAI_API_KEY environment variable")
        return

    # Zero ceremony - just ask
    agent = Agent()
    result = await agent("What is the capital of France?")

    print(f"Response: {result}")
    print(f"Conversation ID: {result.conversation_id}")
    print(f"Response only: {result.response}")


if __name__ == "__main__":
    asyncio.run(main())
