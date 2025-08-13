"""Canonical execution logs - replaces telemetry with beautiful simplicity."""

from typing import Optional


async def logs_command(
    filter_type: Optional[str] = None,
    count: int = 20,
    show_summary: bool = False,
    include_debug: bool = False,
):
    """Handle canonical logs command with consolidated interface."""
    from cogency.events.logs import create_logs_bridge, format_logs_summary

    print("📊 Cogency Execution Logs")
    print("=" * 50)

    # Use existing logs bridge infrastructure
    bridge = create_logs_bridge(None)

    if show_summary:
        # Show summary with event breakdown (consolidated events + summary commands)
        show_logs_summary(bridge, format_logs_summary, include_debug)
    else:
        # Show recent logs with canonical filtering
        show_recent_logs(bridge, count, filter_type, include_debug)


def show_logs_summary(bridge, formatter=None, include_debug=False):
    """Display logs summary with event breakdown."""
    if formatter:
        summary_text = formatter(bridge)
    else:
        summary = bridge.get_summary()
        summary_text = f"📊 Events: {summary.get('total_events', 0)}"

    print(summary_text)

    summary = bridge.get_summary()
    event_types = summary.get("event_types", {})

    if event_types:
        print("\n📊 Event Type Breakdown")
        print("-" * 30)

        # Sort by frequency
        for event_type, count in sorted(event_types.items(), key=lambda x: x[1], reverse=True):
            emoji = bridge._get_event_emoji(event_type, "info", {})
            percentage = (count / summary["total_events"]) * 100 if summary["total_events"] else 0
            print(f"{emoji} {event_type:12} {count:4} ({percentage:4.1f}%)")


def show_recent_logs(
    bridge, count: int, filter_type: Optional[str] = None, include_debug: bool = False
):
    """Display recent logs with filtering."""
    filters = {}

    if filter_type:
        if filter_type == "error":
            filters["errors_only"] = True
        elif filter_type == "state":
            filters["state_mutations"] = True
        elif filter_type == "performance":
            filters["performance"] = True
        else:
            filters["type"] = filter_type

    # When filtering, load more events to ensure matches from persistent logs
    load_count = count * 20 if filter_type else count
    events = bridge.get_recent(load_count, filters, include_debug)

    # Limit final results to requested count
    events = events[-count:] if len(events) > count else events

    if not events:
        print("📭 No recent logs found")
        if filter_type:
            print(f"(filtered by: {filter_type})")
        _show_canonical_filter_help()
        return

    print(f"📋 Recent Logs ({len(events)})")
    if filter_type:
        print(f"Filtered by: {filter_type}")
    print("-" * 50)

    for event in events[-count:]:  # Show most recent
        formatted = bridge.format_event(event, style="compact")
        print(formatted)

    if not filter_type and len(events) >= 10:
        print(
            f"\n💡 Showing last {len(events)} events. Use 'cogency logs --summary' for full session overview."
        )


def _show_canonical_filter_help():
    """Show available filters."""
    print("\n🔍 Available filters:")
    print("  tool        - Tool executions only")
    print("  error       - Errors and warnings only")
    print("  memory      - Memory operations")
    print("  agent       - Agent lifecycle events")
    print("  state       - State mutations (workspace, conversation, profile)")
    print("  performance - Provider costs and timing")
