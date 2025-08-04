#!/usr/bin/env python3
"""Interactive chat with full-capability agent."""

import asyncio

from cogency import Agent


async def main():
    print("🤖 COGENCY")
    print("=" * 20)
    print("I'm Cogency, your AI agent with superpowers!")
    print("I can code, research, analyze data, remember our conversations, and more.")
    print("Type 'quit' to exit.\n")

    # Cogency agent - concise and direct with thinking indicators
    agent = Agent(
        "cogency",
        identity="Cogency - concise, direct, helpful AI. Brief responses unless detail is specifically requested.",
        memory=True,
        console="thinking",  # Show friendly thinking indicators
    )

    while True:
        try:
            user_input = input("👤 ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            if user_input:
                print()  # Newline to separate
                response = await agent.run_async(user_input)
                print(f"🤖 {response}")
                print()

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
