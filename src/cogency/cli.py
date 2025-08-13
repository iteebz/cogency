"""CLI interface."""

import argparse
import asyncio
import inspect
import sys
import time
from pathlib import Path


async def interactive_mode(agent, stream=False, debug=False, timing=False) -> None:
    """Enhanced interactive chat mode."""
    session_start = time.time()
    interaction_count = 0

    print("🔬 Cogency Agent" + (" (Debug Mode)" if debug else ""))
    if stream:
        print("📡 Streaming enabled")
    if timing:
        print("⏱️ Timing enabled")
    print("Type 'exit' to quit")
    print("-" * 40)

    while True:
        try:
            prompt = "🧪 > " if debug else "> "
            message = input(f"\n{prompt}").strip()
            if message.lower() in ["exit", "quit"]:
                break
            if message:
                interaction_count += 1
                interaction_start = time.time()

                if debug:
                    print(f"\n--- Interaction {interaction_count} ---")

                if stream:
                    from cogency.events.streaming import format_stream_event

                    async for event in agent.run_stream(message):
                        formatted = format_stream_event(event)
                        if event.type == "completion":
                            print(f"\n{formatted}")
                        else:
                            print(formatted, flush=True)
                    print()  # Final newline
                else:
                    response = await agent.run_async(message)
                    print(f"\n{response}")

                if timing or debug:
                    interaction_time = time.time() - interaction_start
                    print(f"\n⏱️ Duration: {interaction_time:.2f}s")

                    # Show telemetry in debug mode
                    if debug:
                        show_interaction_telemetry(agent)

        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            if timing or debug:
                total_time = time.time() - session_start
                print(f"📋 Session: {total_time:.1f}s, {interaction_count} interactions")
            break
        except Exception as e:
            print(f"✗ Error: {e}")
            if debug:
                import traceback

                print(f"Debug traceback:\n{traceback.format_exc()}")


async def tools_command(subcommand: str, tool_name: str = None):
    """Handle tool diagnostic commands."""
    from cogency.tools import Files, Recall, Retrieve, Scrape, Search, Shell

    # Setup tools for diagnostics
    tools = [Files(), Shell(), Search(), Scrape(), Recall()]

    # Add Retrieve if configured
    import os

    if retrieval_path := os.getenv("COGENCY_RETRIEVAL_PATH"):
        embeddings_file = Path(retrieval_path).expanduser() / "embeddings.json"
        tools.append(Retrieve(embeddings_path=str(embeddings_file)))

    if subcommand == "list":
        list_tools(tools)
    elif subcommand == "inspect":
        if not tool_name:
            print("Error: --tool-name required for inspect")
            return
        inspect_tool(tools, tool_name)
    elif subcommand == "test":
        await test_tools(tools, tool_name)
    elif subcommand == "benchmark":
        await benchmark_tools(tools)
    elif subcommand == "validate":
        validate_tools(tools)


def list_tools(tools):
    """List all available tools with descriptions."""
    print("🔧 Cogency Tool Registry")
    print("=" * 50)

    for tool in tools:
        emoji = getattr(tool, "emoji", "🔧")
        name = getattr(tool, "name", tool.__class__.__name__)
        description = getattr(tool, "description", "No description available")
        schema = getattr(tool, "schema", "No schema available")
        examples_count = len(getattr(tool, "examples", []))
        rules_count = len(getattr(tool, "rules", []))

        print(f"{emoji} {name.upper()}")
        print(f"   Description: {description}")
        print(f"   Schema: {schema}")
        print(f"   Examples: {examples_count} provided")
        print(f"   Rules: {rules_count} defined")
        print()


def inspect_tool(tools, tool_name: str):
    """Deep inspection of a specific tool."""
    tool = find_tool(tools, tool_name)
    if not tool:
        available = [getattr(t, "name", t.__class__.__name__) for t in tools]
        print(f"❌ Tool '{tool_name}' not found. Available: {available}")
        return

    emoji = getattr(tool, "emoji", "🔧")
    name = getattr(tool, "name", tool.__class__.__name__)

    print(f"🔍 Inspecting {emoji} {name.upper()}")
    print("=" * 50)

    print(f"Description: {getattr(tool, 'description', 'No description')}")
    print(f"Schema: {getattr(tool, 'schema', 'No schema')}")
    print(f"Emoji: {emoji}")

    examples = getattr(tool, "examples", [])
    if examples:
        print(f"\n📋 Examples ({len(examples)}):")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. {example}")

    rules = getattr(tool, "rules", [])
    if rules:
        print(f"\n📜 Rules ({len(rules)}):")
        for i, rule in enumerate(rules, 1):
            print(f"  {i}. {rule}")

    # Show run method signature
    if hasattr(tool, "run"):
        print("\n🔧 Run Method Signature:")
        try:
            sig = inspect.signature(tool.run)
            print(f"  {sig}")
        except Exception as e:
            print(f"  Could not inspect signature: {e}")


async def test_tools(tools, tool_name: str = None):
    """Test tools with basic operations."""
    if tool_name:
        tool = find_tool(tools, tool_name)
        if not tool:
            available = [getattr(t, "name", t.__class__.__name__) for t in tools]
            print(f"❌ Tool '{tool_name}' not found. Available: {available}")
            return
        await test_single_tool(tool)
    else:
        print("🧪 Testing All Tools")
        print("=" * 50)
        for tool in tools:
            await test_single_tool(tool)
            print()


async def test_single_tool(tool):
    """Test a single tool with safe operations."""
    emoji = getattr(tool, "emoji", "🔧")
    name = getattr(tool, "name", tool.__class__.__name__)

    print(f"🧪 Testing {emoji} {name.upper()}")

    try:
        # Basic connectivity/initialization test
        if hasattr(tool, "run"):
            # Try a safe test based on tool type
            if "Files" in tool.__class__.__name__:
                # Test file listing in current directory
                result = await tool.run(action="list", path=".")
                status = "✅" if getattr(result, "success", True) else "❌"
                print(f"   {status} File listing test completed")
            elif "Shell" in tool.__class__.__name__:
                # Test safe echo command
                result = await tool.run(command="echo test")
                status = "✅" if getattr(result, "success", True) else "❌"
                print(f"   {status} Shell echo test completed")
            else:
                print("   ⚠️ No safe test available for this tool type")
        else:
            print("   ⚠️ Tool has no run method")
    except Exception as e:
        print(f"   ❌ Test failed: {e}")


async def benchmark_tools(tools):
    """Run performance benchmarks on tools."""
    print("⚡ Tool Performance Benchmarks")
    print("=" * 50)

    for tool in tools:
        name = getattr(tool, "name", tool.__class__.__name__)

        try:
            if hasattr(tool, "run"):
                times = []
                # Run 3 iterations for average
                for _ in range(3):
                    start = time.time()
                    # Safe benchmark operations
                    if "Files" in tool.__class__.__name__:
                        await tool.run(action="list", path=".")
                    elif "Shell" in tool.__class__.__name__:
                        await tool.run(command="echo benchmark")
                    else:
                        # Skip tools without safe benchmark operations
                        continue
                    times.append((time.time() - start) * 1000)

                if times:
                    avg_time = sum(times) / len(times)
                    print(f"   {name}: {avg_time:.1f}ms avg")
                else:
                    print(f"   {name}: no benchmark available")
            else:
                print(f"   {name}: no run method")
        except Exception as e:
            print(f"   {name}: benchmark failed - {e}")


def validate_tools(tools):
    """Validate tool schemas and required attributes."""
    print("✅ Tool Schema Validation")
    print("=" * 50)

    for tool in tools:
        name = getattr(tool, "name", tool.__class__.__name__)
        print(f"🔍 {name}:")

        # Check required attributes
        required_attrs = ["name", "description"]
        missing = [
            attr for attr in required_attrs if not hasattr(tool, attr) or not getattr(tool, attr)
        ]

        if missing:
            print(f"   ❌ Missing attributes: {missing}")
        else:
            print("   ✅ Basic attributes present")

        # Check for run method
        if hasattr(tool, "run"):
            print("   ✅ Has run method")
        else:
            print("   ❌ Missing run method")

        # Check examples
        examples = getattr(tool, "examples", [])
        if examples:
            print(f"   ✅ {len(examples)} examples defined")
        else:
            print("   ⚠️ No examples defined")


def find_tool(tools, name: str):
    """Find tool by name (case insensitive)."""
    name_lower = name.lower()
    for tool in tools:
        tool_name = getattr(tool, "name", tool.__class__.__name__).lower()
        if tool_name == name_lower or tool.__class__.__name__.lower() == name_lower:
            return tool
    return None


async def telemetry_command(subcommand: str, filter_type: str = None, count: int = 20):
    """Handle telemetry diagnostic commands."""
    from cogency.events import MessageBus, init_bus
    from cogency.events.handlers import EventBuffer
    from cogency.events.telemetry import create_telemetry_bridge, format_telemetry_summary

    print("🔍 Cogency Telemetry System")
    print("=" * 50)

    # Initialize minimal event system for telemetry
    bus = MessageBus()
    buffer = EventBuffer(max_size=1000)
    bus.subscribe(buffer)
    init_bus(bus)

    # Create telemetry bridge
    bridge = create_telemetry_bridge(bus)

    if subcommand == "summary":
        show_telemetry_summary(bridge, format_telemetry_summary)
    elif subcommand == "recent":
        show_recent_events(bridge, count, filter_type)
    elif subcommand == "events":
        show_event_types(bridge)
    elif subcommand == "live":
        print("Live telemetry requires an active agent session.")
        print("Use: cogency --interactive --stream --debug")
        print("Then run queries to see live telemetry.")


def show_telemetry_summary(bridge, formatter=None):
    """Display telemetry summary."""
    if formatter:
        summary_text = formatter(bridge)
    else:
        # Fallback to basic summary
        summary = bridge.get_summary()
        summary_text = f"📊 Events: {summary.get('total_events', 0)}"
    print(summary_text)


def show_recent_events(bridge, count: int, filter_type: str = None):
    """Display recent events with optional filtering."""
    filters = {}
    if filter_type:
        if filter_type == "error":
            filters["errors_only"] = True
        else:
            filters["type"] = filter_type

    events = bridge.get_recent(count, filters)

    if not events:
        print("📭 No recent events found")
        if filter_type:
            print(f"(filtered by: {filter_type})")
        return

    print(f"📋 Recent Events ({len(events)})")
    if filter_type:
        print(f"Filtered by: {filter_type}")
    print("-" * 50)

    for event in events[-count:]:  # Show most recent
        formatted = bridge.format_event(event, style="compact")
        print(formatted)


def show_event_types(bridge):
    """Display available event types and their frequencies."""
    summary = bridge.get_summary()
    event_types = summary.get("event_types", {})

    if not event_types:
        print("📭 No events recorded")
        return

    print("📊 Event Types")
    print("-" * 30)

    # Sort by frequency
    for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
        emoji = bridge._get_event_emoji(event_type, "info", {})
        percentage = (count / summary["total_events"]) * 100 if summary["total_events"] else 0
        print(f"{emoji} {event_type:12} {count:4} ({percentage:4.1f}%)")


def show_interaction_telemetry(agent):
    """Show telemetry for the current interaction."""
    try:
        # Get recent events from agent's logs
        logs = agent.logs(last=10)  # Last 10 events

        if not logs:
            return

        # Show compact event summary
        print("📊 Telemetry:")

        # Count events by type
        event_counts = {}
        tool_events = []
        errors = []

        for event in logs:
            event_type = event.get("type", "unknown")
            event_counts[event_type] = event_counts.get(event_type, 0) + 1

            # Collect specific event types
            data = event.get("data", {})
            if event_type == "tool":
                tool_name = data.get("name", "unknown")
                status = data.get("status", "unknown")
                tool_events.append(f"{tool_name}({status})")
            elif event.get("level") == "error" or data.get("status") == "error":
                errors.append(data.get("error", "unknown error"))

        # Display summary
        summary_parts = []
        for event_type, count in event_counts.items():
            if event_type == "agent":
                continue  # Skip verbose agent events
            summary_parts.append(f"{event_type}:{count}")

        if summary_parts:
            print(f"  Events: {', '.join(summary_parts)}")

        if tool_events:
            tools_str = ", ".join(tool_events)
            print(f"  Tools: {tools_str}")

        if errors:
            print(f"  ❌ Errors: {len(errors)}")
            for error in errors[:2]:  # Show first 2 errors
                print(f"    • {error[:50]}...")

    except Exception:
        # Fail silently - don't break interaction for telemetry issues
        pass


def show_live_telemetry_help():
    """Show help for live telemetry mode."""
    print("🔴 Live Telemetry Mode")
    print("=" * 50)
    print("To see live telemetry during agent execution:")
    print("")
    print("1. Start interactive mode with debug:")
    print("   cogency --interactive --debug")
    print("")
    print("2. Start streaming mode:")
    print("   cogency --interactive --stream")
    print("")
    print("3. Run queries and watch real-time events")
    print("")
    print("Available filters in debug mode:")
    print("  --filter tool     # Show only tool events")
    print("  --filter error    # Show only errors")
    print("  --filter agent    # Show only agent events")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Cogency - Zero ceremony cognitive agents")
    parser.add_argument("message", nargs="*", help="Message for agent")
    parser.add_argument("-i", "--interactive", action="store_true", help="Interactive mode")
    parser.add_argument(
        "--stream", action="store_true", help="Enable streaming responses (with -i)"
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode (with -i)")
    parser.add_argument("--timing", action="store_true", help="Show timing metrics (with -i)")
    parser.add_argument(
        "--tools",
        choices=["list", "inspect", "test", "benchmark", "validate"],
        help="Tool diagnostics",
    )
    parser.add_argument("--tool-name", help="Specific tool name (with --tools)")
    parser.add_argument(
        "--telemetry", choices=["live", "recent", "summary", "events"], help="Show telemetry data"
    )
    parser.add_argument("--filter", help="Filter telemetry by type (e.g., 'tool', 'error')")
    parser.add_argument(
        "--count", type=int, default=20, help="Number of recent events (with --telemetry recent)"
    )
    parser.add_argument("--version", action="version", version="cogency 1.2.2")
    args = parser.parse_args()

    # Handle tool diagnostics
    if args.tools:
        asyncio.run(tools_command(args.tools, args.tool_name))
        return

    # Handle telemetry commands
    if args.telemetry:
        asyncio.run(telemetry_command(args.telemetry, args.filter, args.count))
        return

    # Setup agent with canonical tools
    from cogency import Agent
    from cogency.tools import Files, Recall, Scrape, Search, Shell

    tools = [Files(), Shell(), Search(), Scrape(), Recall()]

    # Add Retrieve if configured
    import os

    if retrieval_path := os.getenv("COGENCY_RETRIEVAL_PATH"):
        from cogency.tools import Retrieve

        embeddings_file = Path(retrieval_path).expanduser() / "embeddings.json"
        tools.append(Retrieve(embeddings_path=str(embeddings_file)))

    try:
        agent = Agent("assistant", tools=tools, memory=True)
    except Exception as e:
        print(f"✗ Error: {e}")
        sys.exit(1)

    # Run
    message = " ".join(args.message) if args.message else ""
    if args.interactive or not message:
        asyncio.run(
            interactive_mode(agent, stream=args.stream, debug=args.debug, timing=args.timing)
        )
    else:
        # Single message mode
        async def run_once():
            response = await agent.run_async(message)
            print(response)

        asyncio.run(run_once())


if __name__ == "__main__":
    main()
