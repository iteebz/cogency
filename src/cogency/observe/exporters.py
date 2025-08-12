"""Essential metrics export - minimal production telemetry."""

import json
import time


class BasicExporter:
    """Minimal metrics export for essential observability."""

    def __init__(self, metrics_handler=None):
        if metrics_handler is None:
            from .handlers import get_metrics_handler

            self.metrics_handler = get_metrics_handler()
        else:
            self.metrics_handler = metrics_handler

    def stats(self) -> dict:
        """Get basic stats summary."""
        if not self.metrics_handler:
            return {}

        stats = self.metrics_handler.stats()
        return {
            "timestamp": time.time(),
            "event_counts": stats.get("event_counts", {}),
            "sessions": stats.get("sessions", {}),
            "performance_summary": self._summarize_performance(stats.get("performance", [])),
        }

    def _summarize_performance(self, performance: list) -> dict:
        """Summarize performance data."""
        if not performance:
            return {}

        tool_timings = [
            p["duration"] for p in performance if p.get("type") == "tool" and p.get("duration")
        ]

        if not tool_timings:
            return {}

        return {
            "tool_count": len(tool_timings),
            "avg_duration": sum(tool_timings) / len(tool_timings),
            "total_duration": sum(tool_timings),
        }

    def export_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.stats(), indent=2)

    def export_simple(self) -> str:
        """Export as simple text format."""
        stats = self.stats()
        lines = [f"Cogency Metrics - {time.ctime(stats.get('timestamp', time.time()))}"]

        # Event counts
        event_counts = stats.get("event_counts", {})
        if event_counts:
            lines.append("\nEvent Counts:")
            for event_type, count in event_counts.items():
                lines.append(f"  {event_type}: {count}")

        # Sessions
        sessions = stats.get("sessions", {})
        if sessions:
            lines.append(f"\nSessions: {sessions.get('total', 0)}")
            if sessions.get("avg_duration"):
                lines.append(f"Average Duration: {sessions['avg_duration']:.2f}s")

        # Performance
        perf = stats.get("performance_summary", {})
        if perf:
            lines.append("\nTool Performance:")
            lines.append(f"  Executions: {perf.get('tool_count', 0)}")
            lines.append(f"  Average: {perf.get('avg_duration', 0):.3f}s")
            lines.append(f"  Total: {perf.get('total_duration', 0):.3f}s")

        return "\n".join(lines)
