"""Observability handlers - unified metrics collection."""

from collections import deque
from typing import Any, Dict


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


# Global singleton
_global_metrics_handler = None


def get_metrics_handler() -> MetricsHandler:
    """Get global metrics handler instance."""
    global _global_metrics_handler
    if _global_metrics_handler is None:
        _global_metrics_handler = MetricsHandler()
    return _global_metrics_handler
