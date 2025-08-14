"""Event logs bridge for CLI access."""

import time
from typing import Any

from .bus import MessageBus
from .handlers import EventBuffer


class LogsBridge:
    """Bridge events to CLI logs."""

    def __init__(self, bus: MessageBus = None):
        self.bus = bus
        self.buffer = EventBuffer(max_size=500)
        self._use_global = bus is None

        if bus:
            bus.subscribe(self.buffer)

    def get_recent(
        self, count: int = 20, filters: dict[str, Any] = None, include_debug: bool = False
    ) -> list[dict[str, Any]]:
        """Get recent events with filtering."""
        if self._use_global:
            # Use global event system
            from .bus import get_logs

            events = get_logs()

            # Fallback to persistent logs if no in-memory events
            if not events:
                # Load more events when filtering to ensure we find matches
                load_count = count * 10 if filters else count
                events = self._load_from_persistent_logs(load_count, include_debug)
        else:
            events = list(self.buffer.events)

        # Apply debug filtering first (constitutional default: hide debug)
        if not include_debug:
            events = [e for e in events if e.get("level", "info") != "debug"]

        # Apply filters
        if filters:
            events = self._apply_filters(events, filters)

        return events[-count:] if count else events

    def get_summary(self) -> dict[str, Any]:
        """Get session summary."""
        if self._use_global:
            # Use global event system
            from .bus import get_logs

            events = get_logs()

            # Fallback to persistent logs if no in-memory events
            if not events:
                events = self._load_from_persistent_logs(
                    1000, include_debug=False
                )  # Load recent events, hide debug
        else:
            events = list(self.buffer.events)

        if not events:
            return {"total_events": 0, "session_start": None}

        # Calculate metrics
        event_types = {}
        tools_used = set()
        iterations = 0
        errors = 0
        start_time = None
        end_time = None

        for event in events:
            event_type = event.get("type")
            event_types[event_type] = event_types.get(event_type, 0) + 1

            # Track timing
            timestamp = event.get("timestamp")
            if timestamp:
                if start_time is None or timestamp < start_time:
                    start_time = timestamp
                if end_time is None or timestamp > end_time:
                    end_time = timestamp

            # Extract metrics directly from event (no nested data field)
            if event_type == "tool" and event.get("status") == "complete":
                tools_used.add(event.get("name", "unknown"))
            elif event_type == "agent" and event.get("state") == "iteration":
                iterations += 1
            elif event.get("level") == "error" or event.get("status") == "error":
                errors += 1

        duration = (end_time - start_time) if (start_time and end_time) else 0

        return {
            "total_events": len(events),
            "event_types": event_types,
            "tools_used": list(tools_used),
            "iterations": iterations,
            "errors": errors,
            "duration": duration,
            "session_start": start_time,
        }

    def format_event(self, event: dict[str, Any], style: str = "compact") -> str:
        """Format event for CLI display."""
        if style == "compact":
            return self._format_compact(event)
        if style == "detailed":
            return self._format_detailed(event)
        if style == "json":
            import json

            return json.dumps(event, default=str, indent=2)
        return str(event)

    def _format_compact(self, event: dict[str, Any]) -> str:
        """Compact single-line event format."""
        timestamp = event.get("timestamp", time.time())
        time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
        event_type = event.get("type", "unknown")
        level = event.get("level", "info")

        # Choose emoji based on event type and level
        emoji = self._get_event_emoji(event_type, level, event)

        # Format content based on event type
        content = self._get_event_content(event_type, event)

        # Level indicator
        level_color = self._get_level_color(level)

        return f"{time_str} {emoji} [{event_type}] {content} {level_color}"

    def _format_detailed(self, event: dict[str, Any]) -> str:
        """Detailed multi-line event format."""
        lines = []
        timestamp = event.get("timestamp", time.time())
        time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))

        # Header
        event_type = event.get("type", "unknown")
        level = event.get("level", "info")
        emoji = self._get_event_emoji(event_type, level, event)

        lines.append(f"{emoji} {event_type.upper()} ({level}) - {time_str}")

        # Event details (no nested data field)
        excluded_keys = {"type", "level", "timestamp"}
        event_data = {k: v for k, v in event.items() if k not in excluded_keys}
        if event_data:
            for key, value in event_data.items():
                if key == "error" and value:
                    lines.append(f"  ❌ Error: {value}")
                elif key == "status":
                    status_emoji = (
                        "✅" if value == "complete" else "⏳" if value == "start" else "❌"
                    )
                    lines.append(f"  {status_emoji} Status: {value}")
                elif key in ["name", "operation", "tool"]:
                    lines.append(f"  🔧 Tool: {value}")
                elif key == "iteration":
                    lines.append(f"  🔄 Iteration: {value}")
                elif key == "response_length":
                    lines.append(f"  📏 Response: {value} chars")
                else:
                    lines.append(f"  • {key}: {value}")

        return "\n".join(lines)

    def _get_event_emoji(self, event_type: str, level: str, event: dict[str, Any]) -> str:
        """Get appropriate emoji for event type and context."""
        if level == "error":
            return "❌"

        emoji_map = {
            "agent": "🧠",
            "tool": "🔧",
            "reason": "💭",
            "respond": "💬",
            "memory": "💾",
            "security": "🔒",
            "config_load": "⚙️",
            "log": "📝",
        }

        emoji = emoji_map.get(event_type, "📊")

        # Context-specific overrides
        if event_type == "tool":
            status = event.get("status")
            if status == "complete":
                emoji = "✅"
            elif status == "error":
                emoji = "❌"
        elif event_type == "agent":
            state = event.get("state")
            if state == "complete":
                emoji = "🎯"
            elif state == "error":
                emoji = "❌"

        return emoji

    def _get_event_content(self, event_type: str, event: dict[str, Any]) -> str:
        """Extract meaningful content from event data."""
        if event_type == "tool":
            # Try data dict first (nested), then direct access (flat)
            data = event.get("data", {})
            name = data.get("name") or event.get("name", "unknown")
            operation = data.get("operation") or event.get("operation")
            status = data.get("status") or event.get("status")
            if operation and operation != name:
                return f"{name}.{operation} → {status}"
            return f"{name} → {status}"

        if event_type == "agent":
            state = event.get("state", "unknown")
            iteration = event.get("iteration")
            if state == "iteration" and iteration is not None:
                return f"iteration {iteration}"
            return state

        if event_type == "reason":
            state = event.get("state", "unknown")
            return f"reasoning → {state}"

        if event_type == "memory":
            operation = event.get("operation", "unknown")
            return f"memory.{operation}"

        if event_type == "security":
            operation = event.get("operation", "assess")
            return f"security.{operation}"

        # Generic content extraction
        important_keys = ["name", "operation", "state", "status", "message"]
        content_parts = []
        for key in important_keys:
            if key in event:
                content_parts.append(str(event[key]))
        return " ".join(content_parts) if content_parts else "event"

    def _get_level_color(self, level: str) -> str:
        """Get color indicator for log level (simplified for CLI)."""
        color_map = {
            "debug": "🔍",
            "info": "",
            "warning": "⚠️",
            "error": "🚨",
        }
        return color_map.get(level, "")

    def _apply_filters(
        self, events: list[dict[str, Any]], filters: dict[str, Any]
    ) -> list[dict[str, Any]]:
        """Apply filters to event list."""
        filtered = events

        if "type" in filters:
            event_type = filters["type"]
            filtered = [e for e in filtered if e.get("type") == event_type]

        if "level" in filters:
            level = filters["level"]
            filtered = [e for e in filtered if e.get("level") == level]

        if "errors_only" in filters and filters["errors_only"]:
            filtered = [
                e for e in filtered if e.get("level") == "error" or e.get("status") == "error"
            ]

        if "since" in filters:
            since = filters["since"]
            filtered = [e for e in filtered if e.get("timestamp", 0) >= since]

        if "tool" in filters:
            tool_name = filters["tool"]
            filtered = [
                e
                for e in filtered
                if e.get("type") == "tool"
                and (e.get("name") == tool_name or e.get("data", {}).get("name") == tool_name)
            ]

        if "state_mutations" in filters and filters["state_mutations"]:
            state_types = ["workspace_saved", "conversation_saved", "profile_saved"]
            filtered = [e for e in filtered if e.get("type") in state_types]

        if "performance" in filters and filters["performance"]:
            perf_types = ["provider", "token_count", "token_cost", "llm", "embed"]
            filtered = [e for e in filtered if e.get("type") in perf_types]

        return filtered

    def _load_from_persistent_logs(
        self, count: int = 100, include_debug: bool = False
    ) -> list[dict[str, Any]]:
        """Load events from persistent JSONL log files as fallback."""
        try:
            import json
            from datetime import datetime, timedelta
            from pathlib import Path

            from cogency.config.paths import paths

            log_dir = Path(paths.logs)
            if not log_dir.exists():
                return []

            events = []

            # Look for recent log files (last 7 days)
            today = datetime.now()
            dates_to_check = [(today - timedelta(days=i)).strftime("%Y%m%d") for i in range(7)]

            for date_str in dates_to_check:
                log_file = log_dir / f"{date_str}.jsonl"
                if log_file.exists():
                    try:
                        with open(log_file) as f:
                            lines = f.readlines()
                            # Get last N lines for efficiency
                            recent_lines = lines[-count:] if len(lines) > count else lines
                            for line in recent_lines:
                                try:
                                    event = json.loads(line.strip())
                                    events.append(event)
                                except json.JSONDecodeError:
                                    continue
                    except Exception:
                        continue

            # Apply debug filtering to retrospective logs (constitutional default: hide debug)
            if not include_debug:
                events = [e for e in events if e.get("level", "info") != "debug"]

            # Sort by timestamp and return most recent
            events.sort(key=lambda x: x.get("timestamp", 0))
            return events[-count:] if len(events) > count else events

        except Exception:
            # Fail gracefully - return empty list if any issues
            return []


def create_logs_bridge(bus: MessageBus = None) -> LogsBridge:
    """Create logs bridge with bus."""
    return LogsBridge(bus)


def format_logs_summary(bridge: LogsBridge) -> str:
    """Format logs summary for CLI display."""
    summary = bridge.get_summary()

    if summary["total_events"] == 0:
        return "📊 No logs data available"

    lines = ["📊 Logs Summary", "=" * 50]

    # Basic metrics
    lines.append(f"Total events: {summary['total_events']}")

    if summary["duration"]:
        lines.append(f"Session duration: {summary['duration']:.1f}s")

    if summary["iterations"]:
        lines.append(f"Reasoning iterations: {summary['iterations']}")

    if summary["errors"]:
        lines.append(f"Errors: {summary['errors']} ❌")

    # Tools used
    if summary["tools_used"]:
        tools_str = ", ".join(summary["tools_used"])
        lines.append(f"Tools used: {tools_str}")

    # Event breakdown
    if summary["event_types"]:
        lines.append("\nEvent Types:")
        for event_type, count in sorted(summary["event_types"].items()):
            emoji = LogsBridge(None)._get_event_emoji(event_type, "info", {})
            lines.append(f"  {emoji} {event_type}: {count}")

    return "\n".join(lines)
