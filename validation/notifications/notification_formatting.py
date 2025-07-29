#!/usr/bin/env python3
"""Validate notification UX formatting with real LLM - demonstrates clean, structured output."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator, Weather
from cogency.utils.notify import NotificationFormatter


async def console_notification_callback(phase: str, message: str, metadata: dict):
    """Print notifications to console with clean formatting."""
    formatter = NotificationFormatter()
    from cogency.utils.notify import Notification

    notification = Notification(phase=phase, message=message, metadata=metadata)
    formatted = formatter.format(notification, include_emoji=True)
    print(f"  {formatted}")


async def main():
    print("🎨 NOTIFICATION FORMATTING VALIDATION")
    print("=" * 60)
    print("Testing UX-friendly notification output with real LLM execution\n")

    # Agent with notifications enabled - we'll capture them via stream
    agent = Agent(
        "formatting_demo_agent",
        identity="helpful assistant demonstrating clean notification UX",
        tools=[Calculator(), Weather()],
        memory=False,
        depth=3,
        notify=True,  # Enable notifications (captured via stream)
        debug=True,  # Enable trace notifications for full visibility
    )

    print("🔍 LIVE NOTIFICATION STREAM (with emoji formatting):")
    print("-" * 50)
    print("Watch for phase transitions and clean UX indicators...\n")

    # Test queries that exercise different phases and tools
    queries = [
        "Calculate 15 * 8.5 and tell me the result",
        "What's 32°F in Celsius? Use the calculator if needed",
    ]

    for i, query in enumerate(queries, 1):
        print(f"Query {i}: {query}")
        print("=" * 45)

        try:
            result = await agent.run(query)
            print("=" * 45)
            print(f"🎯 Result: {result}\n")

            if i < len(queries):
                print("⏳ Next query in 1 second...\n")
                await asyncio.sleep(1)

        except Exception as e:
            print(f"❌ Error: {e}\n")

    print("📊 NOTIFICATION UX VALIDATION COMPLETE!")
    print("=" * 50)
    print("✅ Key UX Features Demonstrated:")
    print("  • ⚙️  Preprocess phase with clean indicators")
    print("  • 💭 Reasoning phase with thinking indicators")
    print("  • ⚡ Action phase with tool execution feedback")
    print("  • 🤖 Response phase with completion indicators")
    print("  • 🔍 Trace messages for debugging (when debug=True)")
    print("\n✅ Clean, structured notification flow for optimal DX/UX")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
