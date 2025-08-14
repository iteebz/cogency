#!/usr/bin/env python3
"""Execution flow debugging - trace Agent execution for Claude."""

import asyncio

from cogency import Agent


async def main():
    """Trace Agent execution flow."""
    print("=== EXECUTION FLOW DEBUG ===")

    # Create agent
    agent = Agent("assistant")

    # Run simple query
    print("Running test query...")
    response = await agent.run("What is 2+2?")

    # Check if agent has logs method
    if hasattr(agent, "logs") and callable(agent.logs):
        logs = agent.logs()
        print(f"\nExecution events: {len(logs)}")

        # Show event types
        event_types = {}
        for log in logs:
            event_type = log.get("type", "unknown")
            event_types[event_type] = event_types.get(event_type, 0) + 1

        print("Event breakdown:")
        for event_type, count in event_types.items():
            print(f"  {event_type}: {count}")

        # Show recent events
        print("\nRecent events:")
        for log in logs[-5:]:
            event_type = log.get("type", "unknown")
            content = str(log.get("content", ""))[:50]
            print(f"  {event_type}: {content}...")
    else:
        print("\nNo logging available in current Agent implementation")

    print(f"\nResponse: {response[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
