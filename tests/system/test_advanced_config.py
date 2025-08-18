"""System Test: Advanced Configuration Capability Baseline"""

import asyncio

from cogency import BASIC_TOOLS, Agent, profile


async def main():
    # Advanced configuration
    profile(
        "researcher",
        name="Dr. Sarah Chen",
        preferences=["detailed analysis", "scientific accuracy"],
        context="Research scientist specializing in AI",
    )

    agent = Agent(
        tools=BASIC_TOOLS,
        max_iterations=10,  # Allow more reasoning cycles
    )

    # Complex research task
    result = await agent(
        "Research the latest developments in transformer architecture "
        "and create a summary document with key findings",
        user_id="researcher",
    )

    print(f"Research result: {result}")
    print(f"Conversation: {result.conversation_id}")

    # Demonstrate property access
    print(f"Response property: {result.response[:100]}...")
    print(f"Conversation ID property: {result.conversation_id}")


if __name__ == "__main__":
    asyncio.run(main())
