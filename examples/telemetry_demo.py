#!/usr/bin/env python3
"""CLI Telemetry Integration Demo

Demonstrates comprehensive telemetry surfacing through cogency.cli interface.
Shows event capture, filtering, and beautiful visualization.

Usage:
    python telemetry_demo.py
"""

from cogency import Agent
from cogency.events import create_telemetry_bridge, format_telemetry_summary
from cogency.events.bus import _bus


def demo_telemetry_system():
    """Demonstrate CLI telemetry integration capabilities."""

    print("🔍 CLI TELEMETRY INTEGRATION DEMO")
    print("=" * 60)
    print()

    # Create agent with telemetry
    agent = Agent("telemetry_demo", tools=[], memory=False)

    # Get telemetry bridge from agent's event bus
    bridge = create_telemetry_bridge(_bus)

    print("1️⃣ Agent created with telemetry bridge")
    print(f"   Event bus initialized: {_bus is not None}")
    print(f"   Telemetry bridge ready: {bridge is not None}")
    print()

    # Demo 1: Basic telemetry with simple query
    print("2️⃣ Running simple query...")
    try:
        # Use sync version to avoid event loop issues in demo
        response = agent.run("What are the key principles of software architecture?")
        print(f"   ✅ Response: {response[:80]}...")
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:80]}...")

    # Show immediate telemetry
    summary = bridge.get_summary()
    print(f"   📊 Events captured: {summary['total_events']}")
    print()

    # Demo 2: Show recent events
    print("3️⃣ Recent events (compact format):")
    recent_events = bridge.get_recent(count=5)
    for event in recent_events:
        formatted = bridge.format_event(event, style="compact")
        print(f"   {formatted}")
    print()

    # Demo 3: Event filtering
    print("4️⃣ Filtering events by type:")
    agent_events = bridge.get_recent(filters={"type": "agent"})
    print(f"   Agent events: {len(agent_events)}")

    tool_events = bridge.get_recent(filters={"type": "tool"})
    print(f"   Tool events: {len(tool_events)}")

    reason_events = bridge.get_recent(filters={"type": "reason"})
    print(f"   Reason events: {len(reason_events)}")
    print()

    # Demo 4: Detailed event format
    print("5️⃣ Detailed event format (last event):")
    if recent_events:
        detailed = bridge.format_event(recent_events[-1], style="detailed")
        print(f"   {detailed}")
    print()

    # Demo 5: Error simulation and telemetry
    print("6️⃣ Simulating error condition...")
    try:
        # This will likely cause an error due to missing API key or other issues
        error_response = agent.run("This query will demonstrate error telemetry")
        print(f"   Unexpected success: {error_response[:50]}...")
    except Exception as e:
        print(f"   ✅ Expected error occurred: {str(e)[:50]}...")

    # Check for error events
    error_events = bridge.get_recent(filters={"errors_only": True})
    print(f"   📊 Error events captured: {len(error_events)}")
    print()

    # Demo 6: Complete telemetry summary
    print("7️⃣ Complete telemetry summary:")
    summary_text = format_telemetry_summary(bridge)
    # Indent each line for better display
    indented_summary = "\n".join(f"   {line}" for line in summary_text.split("\n"))
    print(indented_summary)
    print()

    # Demo 7: Show event type distribution
    print("8️⃣ Event type distribution:")
    final_summary = bridge.get_summary()
    event_types = final_summary.get("event_types", {})
    total = final_summary.get("total_events", 1)

    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
        emoji = bridge._get_event_emoji(event_type, "info", {})
        percentage = (count / total) * 100
        print(f"   {emoji} {event_type:12} {count:3} ({percentage:5.1f}%)")
    print()

    print("🎯 CLI Telemetry Integration Demo Complete!")
    print()
    print("💡 Try these commands in your terminal:")
    print("   cogency --telemetry summary")
    print("   cogency --telemetry recent")
    print("   cogency --telemetry events")
    print("   cogency --interactive --debug  # for real-time telemetry")


def demo_cli_commands():
    """Show CLI command examples."""
    print()
    print("📋 CLI TELEMETRY COMMANDS")
    print("=" * 40)
    print()

    commands = [
        ("cogency --telemetry summary", "Show session metrics and overview"),
        ("cogency --telemetry recent", "Display recent events with timestamps"),
        ("cogency --telemetry events", "Event type breakdown with percentages"),
        ("cogency --telemetry recent --filter tool", "Show only tool events"),
        ("cogency --telemetry recent --filter error", "Show only error events"),
        ("cogency --telemetry recent --count 50", "Show last 50 events"),
        ("cogency --interactive --debug", "Interactive mode with real-time telemetry"),
        ("cogency --interactive --stream", "Streaming mode with event correlation"),
    ]

    for command, description in commands:
        print(f"💻 {command}")
        print(f"   {description}")
        print()


if __name__ == "__main__":
    print("🚀 Starting CLI Telemetry Integration Demo...")
    print("   This demo shows comprehensive event surfacing capabilities")
    print("   integrated into the cogency.cli interface.")
    print()

    # Run the demo
    try:
        demo_telemetry_system()
        demo_cli_commands()

        print("✅ Demo completed successfully!")
        print("   Check docs/dev/telemetry.md for complete documentation")

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        print("   Note: This is expected if no LLM API key is configured")
        print("   The telemetry system works regardless of LLM success/failure")
