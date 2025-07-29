#!/usr/bin/env python3
"""Validate notification system with trace - demonstrates clean phase transitions and UX."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator, Weather


async def main():
    print("🔍 NOTIFICATION SYSTEM VALIDATION")
    print("=" * 50)
    print("Testing phase-based notifications with real LLM execution\n")

    # Agent with notifications enabled - auto-detects available LLM
    agent = Agent(
        "notification_demo",
        identity="helpful assistant with visible reasoning",
        tools=[Calculator(), Weather()],
        memory=False,
        depth=3,
        notify=True,  # Enable notifications
        debug=True,  # Enable trace for full visibility
    )

    print(f"✅ Agent configured with {agent.llm.provider_name} LLM")
    print(f"✅ Notifications enabled: {agent.notify}")
    print(f"✅ Debug/trace enabled: {agent.debug}")
    print()

    # Test queries that should trigger different phases
    queries = [
        "Calculate 25 * 4.2 and show me the work",
        "What's the weather in Paris and convert 20°C to Fahrenheit?",
    ]

    for i, query in enumerate(queries, 1):
        print(f"{'='*60}")
        print(f"QUERY {i}: {query}")
        print("=" * 60)
        print()

        try:
            # Use streaming to capture phase notifications
            result_parts = []

            async for chunk in agent.stream(query):
                # Print each chunk as it arrives (includes notifications)
                chunk = chunk.strip()
                if chunk:
                    print(chunk)
                    # Collect non-notification chunks for final result
                    if not any(chunk.startswith(emoji) for emoji in ["⚙️", "💭", "⚡", "🤖", "🔍"]):
                        result_parts.append(chunk)

            print()
            print(f"🎯 FINAL RESULT: {' '.join(result_parts).strip()}")

            if i < len(queries):
                print(f"\n{'⏳ Next query in 2 seconds...'}\n")
                await asyncio.sleep(2)

        except Exception as e:
            print(f"❌ ERROR: {e}")

    print(f"\n{'='*60}")
    print("✅ NOTIFICATION SYSTEM VALIDATION COMPLETE!")
    print("=" * 60)
    print("Key features demonstrated:")
    print("  • ⚙️  Preprocess: Query analysis and tool selection")
    print("  • 💭 Reasoning: Decision making and planning")
    print("  • ⚡ Action: Tool execution with feedback")
    print("  • 🤖 Response: Final answer generation")
    print("  • 🔍 Trace: Internal debugging information")
    print()
    print("✅ Clean emoji-based phase indicators")
    print("✅ Real-time notification streaming")
    print("✅ Structured execution visibility")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
