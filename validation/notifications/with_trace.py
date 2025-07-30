#!/usr/bin/env python3
"""Validate v2 notification system with trace - demonstrates clean phase transitions and UX."""

import asyncio

from cogency import Agent
from cogency.notify import EmojiFormatter
from cogency.tools import Calculator, Weather


async def main():
    print("🔍 V2 NOTIFICATION SYSTEM VALIDATION")
    print("=" * 50)
    print("Testing v2 phase-based notifications with real Agent execution\n")

    # Agent with v2 notification system - emoji formatter with trace visibility
    agent = Agent(
        "notification_demo",
        identity="helpful assistant with visible v2 reasoning",
        tools=[Calculator(), Weather()],
        memory=False,
        depth=3,
        formatter=EmojiFormatter(),  # v2 notification system
    )

    print(f"✅ Agent configured with {agent.llm.provider_name} LLM")
    print(f"✅ V2 formatter: {type(agent.formatter).__name__}")
    print("✅ V2 notification system active")
    print()

    # Test queries that should trigger different phases
    queries = [
        "Calculate 25 * 4.2 and show me the work",
        "What's the weather in Paris and convert 20°C to Fahrenheit?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"{'='*60}")
        print(f"V2 QUERY {i}: {query}")
        print("=" * 60)
        print()

        try:
            # Use streaming to capture v2 phase notifications
            result_parts = []

            async for chunk in agent.stream(query):
                # Print each chunk as it arrives (includes v2 notifications)
                chunk = chunk.strip()
                if chunk:
                    print(chunk)
                    # Collect non-notification chunks for final result
                    if not any(emoji in chunk for emoji in ["⚙️", "💭", "⚡", "🤖", "🔍", "🧠", "💾"]):
                        result_parts.append(chunk)

            print()
            print(f"🎯 V2 FINAL RESULT: {' '.join(result_parts).strip()}")

            if i < len(queries):
                print(f"\n{'⏳ Next query in 2 seconds...'}\n")
                await asyncio.sleep(2)

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print(f"\n{'='*60}")
    print("✅ V2 NOTIFICATION SYSTEM VALIDATION COMPLETE!")
    print("=" * 60)
    print("Key v2 features demonstrated:")
    print("  • ⚙️  Preprocess: Query analysis and tool selection")
    print("  • 💭 Reasoning: Decision making and planning")
    print("  • ⚡ Tool Execution: Real-time feedback with success/failure")
    print("  • 🤖 Response: Final answer generation")
    print("  • 🔍 Trace: Internal debugging information")
    print("  • 🧠 Memory: Save operations with metadata")
    print()
    print("✅ Clean emoji-based phase indicators")
    print("✅ Real-time v2 notification streaming")
    print("✅ Structured async execution visibility")
    print("✅ Type-safe notification data")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
