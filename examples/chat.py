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

    # Cogency agent - concise and direct
    agent = Agent(
        "cogency",
        identity="Cogency - concise, direct, helpful AI. Brief responses unless detail is specifically requested.",
        memory=True,
    )

    while True:
        try:
            user_input = input("👤 ").strip()
            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            if user_input:
                print()  # Newline to separate
                response_started = False
                async for chunk in agent.stream(user_input):
                    # Detect when actual response starts (not thinking/tools)
                    if not response_started:
                        if chunk.startswith(
                            (
                                "\n🧠",
                                "\n⚡",
                                "\n🔍",
                                "\n📁",
                                "\n🚀",
                                "\n💾",
                                "\n🛠️",
                                "\n🌐",
                                "\n⏰",
                                "\n📊",
                                "\n🧮",
                                " ↳",
                            )
                        ):
                            # This is thinking/tool output - just print it
                            print(chunk, end="", flush=True)
                        else:
                            # This is the start of the actual response
                            print("\n", end="", flush=True)
                            print(chunk, end="", flush=True)
                            response_started = True
                    else:
                        # Already in response mode
                        print(chunk, end="", flush=True)
                print("\n")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break


if __name__ == "__main__":
    asyncio.run(main())
