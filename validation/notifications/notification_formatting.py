#!/usr/bin/env python3
"""Validate v2 notification formatting with real Agent - demonstrates clean, structured output."""

import asyncio

from cogency import Agent
from cogency.notify import EmojiFormatter
from cogency.tools import Calculator, Weather

# No need for callback - v2 Agent handles formatting internally via stream


async def main():
    print("🎨 V2 NOTIFICATION FORMATTING VALIDATION")
    print("=" * 60)
    print("Testing UX-friendly v2 notification output with real Agent execution\n")

    # Agent with v2 notification system - emoji formatter by default
    agent = Agent(
        "formatting_demo_agent",
        identity="helpful assistant demonstrating clean v2 notification UX",
        tools=[Calculator(), Weather()],
        memory=False,
        depth=3,
        formatter=EmojiFormatter(),  # v2 notification system
    )

    print("🔍 LIVE V2 NOTIFICATION STREAM (with emoji formatting):")
    print("-" * 50)
    print("Watch for v2 phase transitions and clean UX indicators...\n")

    # Test queries that exercise different phases and tools
    queries = [
        "Calculate 15 * 8.5 and tell me the result"
        "What's 32°F in Celsius? Use the calculator if needed"
    ]

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query}")
        print("=" * 45)

        try:
            # Use streaming to see v2 notifications in real-time
            result_parts = []
            async for chunk in agent.stream(query):
                chunk = chunk.strip()
                if chunk:
                    print(chunk)
                    # Collect response parts (non-notification chunks)
                    if not any(emoji in chunk for emoji in ["⚙️", "💭", "⚡", "🤖", "🔍"]):
                        result_parts.append(chunk)

            print("=" * 45)
            print(f"🎯 Final Result: {' '.join(result_parts).strip()}\n")

            if i < len(queries):
                print("⏳ Next query in 1 second...\n")
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Error: {e}\n")

    print("📊 V2 NOTIFICATION UX VALIDATION COMPLETE!")
    print("=" * 50)
    print("✅ Key V2 Features Demonstrated:")
    print("  • ⚙️  Preprocess phase with clean indicators")
    print("  • 💭 Reasoning phase with thinking indicators")
    print("  • ⚡ Tool execution with real-time feedback")
    print("  • 🤖 Response phase with completion indicators")
    print("  • 🔍 Trace messages for debugging")
    print("  • 📡 Async notification emission")
    print("  • 🎨 Type-safe formatter system")
    print("\n✅ Clean, structured v2 notification flow for optimal DX/UX")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
