"""Event consumption handlers - extensible business logic."""

from collections import deque
from typing import Any, Dict, List


class ConsoleHandler:
    """Clean real-time user feedback - no dual system mess."""

    def __init__(self, enabled: bool = True, debug: bool = False):
        self.enabled = enabled
        self.debug = debug

    def handle(self, event):
        """Handle notification events with clean output."""
        if not self.enabled:
            return

        event_type = event["type"]
        data = event["data"]

        # Agent lifecycle
        if event_type == "start":
            query = data.get("query", "")
            print("🚀 Starting agent...")
            if query and len(query) < 100:
                print(f"📝 {query}")

        elif event_type == "agent_create":
            name = data.get("name", "agent")
            status = data.get("status", "")
            if status == "complete":
                print(f"✅ Agent '{name}' ready")

        # Processing steps
        elif event_type == "triage":
            state = data.get("state", "")
            if state == "complete":
                tools = data.get("selected_tools", 0)
                if tools:
                    print(f"🔧 Selected {tools} tools")
                else:
                    print("💭 Direct response")

        elif event_type == "reason":
            state = data.get("state", "")
            if state in ["planning", "analyzing"]:
                print(f"🧠 {state.title()}...")

        elif event_type == "action":
            tool = data.get("tool", "tool")
            print(f"⚡ Using {tool}")

        elif event_type == "respond":
            state = data.get("state", "")
            if state == "generating":
                print("📝 Generating...")
            elif state == "complete":
                print("✅ Response ready")

        # Tools
        elif event_type == "tool":
            name = data.get("name", "tool")
            duration = data.get("duration", 0)
            if data.get("ok"):
                print(f"✅ {name}" + (f" ({duration:.1f}s)" if duration > 0 else ""))
            else:
                print(f"❌ {name} failed")

        # System
        elif event_type == "error":
            message = data.get("message", "Error")
            print(f"❌ {message}")

        elif event_type == "debug" and self.debug:
            message = data.get("message", "Debug")
            print(f"🐛 {message}")

        # Config (quiet unless debug)
        elif event_type == "config_load" and self.debug:
            component = data.get("component", "component")
            status = data.get("status", "")
            if status == "complete":
                print(f"⚙️  {component} loaded")


class LoggerHandler:
    """Centralized structured logging with rolling buffer for agent.logs()."""

    def __init__(self, max_size: int = 1000, structured: bool = True):
        self.events = deque(maxlen=max_size)
        self.structured = structured
        self.config = {
            "max_size": max_size,
            "include_timestamps": True,
            "include_metadata": True,
            "filter_noise": True,  # Skip config_load events by default
        }

    def handle(self, event):
        """Store event with optional filtering."""
        # Filter noise unless debug mode
        if (
            self.config["filter_noise"]
            and event["type"] == "config_load"
            and event["data"].get("status") in ["loading", "complete"]
        ):
            return

        # Store structured event
        if self.structured:
            structured_event = {
                "timestamp": event["timestamp"],
                "type": event["type"],
                **event["data"],  # Flatten data into root level
            }
            self.events.append(structured_event)
        else:
            self.events.append(event)

    def logs(self) -> List[Dict[str, Any]]:
        """Return all stored events in structured format."""
        return list(self.events)

    def configure(self, **options):
        """Update handler configuration."""
        self.config.update(options)


class MetricsHandler:
    """Clean stats collection - separate from decorator timing mess."""

    def __init__(self, max_timings: int = 1000):
        # Core counters - no decorator confusion
        self.counters = {}
        self.performance = deque(maxlen=max_timings)
        self.sessions = deque(maxlen=100)  # Agent session metrics

        # Current session tracking
        self.current_session = None

    def handle(self, event):
        """Collect clean metrics from bus events only."""
        event_type = event["type"]
        data = event["data"]
        timestamp = event["timestamp"]

        # Count all events
        self.counters[event_type] = self.counters.get(event_type, 0) + 1

        # Session tracking
        if event_type == "start":
            self.current_session = {
                "start_time": timestamp,
                "query": data.get("query", ""),
                "tools_used": 0,
                "reasoning_steps": 0,
                "errors": 0,
            }

        elif event_type == "tool" and self.current_session:
            self.current_session["tools_used"] += 1
            # Track tool performance separately
            duration = data.get("duration", 0)
            success = data.get("ok", False)
            self.performance.append(
                {
                    "type": "tool",
                    "name": data.get("name", "unknown"),
                    "duration": duration,
                    "success": success,
                    "timestamp": timestamp,
                }
            )

        elif event_type == "reason" and self.current_session:
            self.current_session["reasoning_steps"] += 1

        elif event_type == "error" and self.current_session:
            self.current_session["errors"] += 1

        elif event_type == "respond" and data.get("state") == "complete" and self.current_session:
            # Session complete
            self.current_session["end_time"] = timestamp
            self.current_session["duration"] = timestamp - self.current_session["start_time"]
            self.sessions.append(self.current_session.copy())
            self.current_session = None

    def stats(self) -> Dict[str, Any]:
        """Return clean metrics - no decorator pollution."""
        recent_sessions = list(self.sessions)[-10:]  # Last 10 sessions
        avg_duration = (
            sum(s.get("duration", 0) for s in recent_sessions) / len(recent_sessions)
            if recent_sessions
            else 0
        )

        return {
            "event_counts": dict(self.counters),
            "performance": list(self.performance)[-50:],  # Last 50 operations
            "sessions": {
                "total": len(self.sessions),
                "recent": recent_sessions,
                "avg_duration": avg_duration,
                "current": self.current_session,
            },
        }

    def tool_stats(self) -> Dict[str, Any]:
        """Specific tool performance metrics."""
        tool_data = {}
        for perf in self.performance:
            if perf["type"] == "tool":
                name = perf["name"]
                if name not in tool_data:
                    tool_data[name] = {"calls": 0, "successes": 0, "total_duration": 0}

                tool_data[name]["calls"] += 1
                if perf["success"]:
                    tool_data[name]["successes"] += 1
                tool_data[name]["total_duration"] += perf["duration"]

        # Calculate averages
        for _name, data in tool_data.items():
            data["success_rate"] = data["successes"] / data["calls"] if data["calls"] > 0 else 0
            data["avg_duration"] = (
                data["total_duration"] / data["calls"] if data["calls"] > 0 else 0
            )

        return tool_data


class CallbackHandler:
    """Execute custom callback for each event - websockets, streaming, etc."""

    def __init__(self, callback):
        """Initialize with callback function.

        Args:
            callback: Function called with each event dict
        """
        self.callback = callback

    def handle(self, event):
        """Execute callback with event data."""
        if self.callback:
            self.callback(event)
