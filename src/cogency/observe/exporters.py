"""Beautiful telemetry exporters - read from unified event system."""

import json
import time
from typing import Dict, List


class Prometheus:
    """Export metrics in Prometheus format - reads from MetricsHandler."""

    def __init__(self, metrics_handler=None):
        if metrics_handler is None:
            from .handlers import get_metrics_handler

            self.metrics_handler = get_metrics_handler()
        else:
            self.metrics_handler = metrics_handler

    def export(self) -> str:
        """Export agent metrics in proper Prometheus format."""
        if not self.metrics_handler:
            return ""

        stats = self.metrics_handler.stats()
        lines = []

        # Export event counts as counters
        event_counts = stats.get("event_counts", {})
        if event_counts:
            lines.append("# HELP cogency_events_total Total agent events by type")
            lines.append("# TYPE cogency_events_total counter")
            for event_type, count in event_counts.items():
                lines.append(f'cogency_events_total{{type="{event_type}"}} {count}')

        # Export tool performance
        performance = stats.get("performance", [])
        timing_data = [p for p in performance if p.get("type") == "tool" and p.get("duration")]

        if timing_data:
            lines.append("")
            lines.append("# HELP cogency_tool_duration_seconds Tool execution duration")
            lines.append("# TYPE cogency_tool_duration_seconds histogram")

            durations = [p["duration"] for p in timing_data]
            count = len(durations)
            total = sum(durations)

            lines.extend(
                [
                    f"cogency_tool_duration_seconds_count {count}",
                    f"cogency_tool_duration_seconds_sum {total:.6f}",
                    f'cogency_tool_duration_seconds_bucket{{le="0.1"}} {len([d for d in durations if d <= 0.1])}',
                    f'cogency_tool_duration_seconds_bucket{{le="1.0"}} {len([d for d in durations if d <= 1.0])}',
                    f'cogency_tool_duration_seconds_bucket{{le="10.0"}} {len([d for d in durations if d <= 10.0])}',
                    f'cogency_tool_duration_seconds_bucket{{le="+Inf"}} {count}',
                ]
            )

        # Export session metrics
        sessions = stats.get("sessions", {})
        if sessions.get("total"):
            lines.append("")
            lines.append("# HELP cogency_sessions_total Total completed agent sessions")
            lines.append("# TYPE cogency_sessions_total counter")
            lines.append(f"cogency_sessions_total {sessions['total']}")

            if sessions.get("avg_duration"):
                lines.append("")
                lines.append(
                    "# HELP cogency_session_duration_avg Average session duration in seconds"
                )
                lines.append("# TYPE cogency_session_duration_avg gauge")
                lines.append(f"cogency_session_duration_avg {sessions['avg_duration']:.6f}")

        return "\n".join(lines) + "\n" if lines else ""


class OpenTelemetry:
    """Export metrics in OpenTelemetry format - reads from MetricsHandler."""

    def __init__(self, metrics_handler=None, service_name: str = "cogency"):
        if metrics_handler is None:
            from .handlers import get_metrics_handler

            self.metrics_handler = get_metrics_handler()
        else:
            self.metrics_handler = metrics_handler
        self.service_name = service_name

    def export(self) -> Dict:
        """Export all metrics as OpenTelemetry JSON format."""
        if not self.metrics_handler:
            return {"resourceMetrics": []}

        timestamp_ns = int(time.time() * 1_000_000_000)
        stats = self.metrics_handler.stats()

        resource_metrics = {
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": self.service_name}},
                    {"key": "service.version", "value": {"stringValue": "1.0.0"}},
                ]
            },
            "scopeMetrics": [
                {
                    "scope": {"name": "cogency.observe", "version": "1.0.0"},
                    "metrics": self._export_metrics(stats, timestamp_ns),
                }
            ],
        }

        return {"resourceMetrics": [resource_metrics]}

    def _export_metrics(self, stats: Dict, timestamp_ns: int) -> List[Dict]:
        """Export all metric types from MetricsHandler stats."""
        metrics = []

        # Export event counts as counters
        for event_type, count in stats.get("event_counts", {}).items():
            metrics.append(
                {
                    "name": f"cogency.{event_type}",
                    "description": f"Cogency {event_type} event count",
                    "unit": "1",
                    "sum": {
                        "dataPoints": [
                            {
                                "timeUnixNano": timestamp_ns,
                                "asInt": count,
                                "isMonotonic": True,
                            }
                        ],
                        "aggregationTemporality": 2,  # CUMULATIVE
                    },
                }
            )

        # Export tool performance as histogram
        performance = stats.get("performance", [])
        timing_data = [p for p in performance if p.get("type") == "tool" and p.get("duration")]

        if timing_data:
            durations = [p["duration"] for p in timing_data]
            count = len(durations)
            total = sum(durations)

            metrics.append(
                {
                    "name": "cogency.tool_duration",
                    "description": "Tool execution duration histogram",
                    "unit": "s",
                    "histogram": {
                        "dataPoints": [
                            {
                                "timeUnixNano": timestamp_ns,
                                "count": str(count),
                                "sum": total,
                                "bucketCounts": [
                                    str(len([d for d in durations if d <= 0.1])),
                                    str(len([d for d in durations if d <= 1.0])),
                                    str(len([d for d in durations if d <= 10.0])),
                                    str(count),
                                ],
                                "explicitBounds": [0.1, 1.0, 10.0],
                            }
                        ],
                        "aggregationTemporality": 2,  # CUMULATIVE
                    },
                }
            )

        # Export session metrics
        sessions = stats.get("sessions", {})
        if sessions.get("total"):
            metrics.append(
                {
                    "name": "cogency.sessions",
                    "description": "Total agent sessions",
                    "unit": "1",
                    "sum": {
                        "dataPoints": [
                            {
                                "timeUnixNano": timestamp_ns,
                                "asInt": sessions["total"],
                                "isMonotonic": True,
                            }
                        ],
                        "aggregationTemporality": 2,  # CUMULATIVE
                    },
                }
            )

        return metrics

    def export_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.export(), indent=2)
