#!/usr/bin/env python3
"""Interactive testing script with full debug and notifications."""

import asyncio
import time

from cogency import Agent
from cogency.tools import Files, Shell, Search, Scrape
from cogency.tools.recall import Recall


async def main():
    print("🔬 COGENCY INTERACTIVE TESTING")
    print("=" * 40)
    print("Beautiful notifications enabled automatically")
    print("Type 'quit' to exit\n")

    # Zero-config: automatic beautiful notifications
    agent = Agent("test-agent", tools=[Files(), Shell(), Search(), Scrape(), Recall()], memory=True, debug=True)

    session_start = time.time()
    interaction_count = 0

    while True:
        try:
            user_input = input("🧪 Test> ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("🏁 Testing complete!")
                print_session_summary(session_start, interaction_count)
                break

            if user_input:
                interaction_count += 1
                interaction_start = time.time()
                print(f"\n--- Interaction {interaction_count} ---")

                async for chunk in agent.stream(user_input):
                    print(chunk, end="", flush=True)

                interaction_time = time.time() - interaction_start
                print(f"\n⏱️  Duration: {interaction_time:.2f}s\n")

        except KeyboardInterrupt:
            print("\n🛑 Interrupted")
            print_session_summary(session_start, interaction_count)
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Continuing...\n")


def print_session_summary(start_time: float, interactions: int):
    """Print session summary."""
    total_time = time.time() - start_time
    print(f"\n📋 Session: {total_time:.1f}s, {interactions} interactions")


if __name__ == "__main__":
    asyncio.run(main())
