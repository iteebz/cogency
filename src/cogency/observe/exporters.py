"""Beautiful telemetry exporters - Prometheus() and OpenTelemetry()."""

import json
import time
from typing import Dict, List, Optional

from .metrics import Metrics, MetricsSummary


class Prometheus:
    """Export metrics in Prometheus format with zero ceremony."""

    def __init__(self, metrics: Optional[Metrics] = None):
        from .metrics import get_metrics

        self.metrics = metrics or get_metrics()

    def export(self) -> str:
        """Export all metrics as Prometheus format."""
        lines = []
        timestamp_ms = int(time.time() * 1000)

        # Export counters
        for key, value in self.metrics.counters.items():
            name, tags = self._parse_key(key)
            metric_name = f"cogency_{name}_total"
            labels = self._format_labels(tags)
            lines.append(f"{metric_name}{labels} {value} {timestamp_ms}")

        # Export gauges
        for key, value in self.metrics.gauges.items():
            name, tags = self._parse_key(key)
            metric_name = f"cogency_{name}"
            labels = self._format_labels(tags)
            lines.append(f"{metric_name}{labels} {value} {timestamp_ms}")

        # Export histogram summaries
        for summary in self.metrics.all_summaries():
            base_name = f"cogency_{summary.name}"
            labels = self._format_labels(summary.tags)

            # Prometheus histogram format
            lines.extend(
                [
                    f"{base_name}_count{labels} {summary.count} {timestamp_ms}",
                    f"{base_name}_sum{labels} {summary.sum} {timestamp_ms}",
                    f'{base_name}_bucket{{le="0.5"}}{labels} {self._bucket_count(summary, 0.5)} {timestamp_ms}',
                    f'{base_name}_bucket{{le="0.95"}}{labels} {self._bucket_count(summary, 0.95)} {timestamp_ms}',
                    f'{base_name}_bucket{{le="0.99"}}{labels} {self._bucket_count(summary, 0.99)} {timestamp_ms}',
                    f'{base_name}_bucket{{le="+Inf"}}{labels} {summary.count} {timestamp_ms}',
                ]
            )

        return "\n".join(lines) + "\n" if lines else ""

    def _parse_key(self, key: str) -> tuple:
        """Parse metric key into name and tags."""
        return self.metrics._parse(key)

    def _format_labels(self, tags: Dict[str, str]) -> str:
        """Format tags as Prometheus labels."""
        if not tags:
            return ""

        label_pairs = [f'{k}="{v}"' for k, v in sorted(tags.items())]
        return "{" + ",".join(label_pairs) + "}"

    def _bucket_count(self, summary: MetricsSummary, le: float) -> int:
        """Estimate bucket count for histogram."""
        if le >= 0.99:
            return int(summary.count * 0.99)
        elif le >= 0.95:
            return int(summary.count * 0.95)
        elif le >= 0.5:
            return int(summary.count * 0.5)
        return 0


class OpenTelemetry:
    """Export metrics in OpenTelemetry format with zero ceremony."""

    def __init__(self, metrics: Optional[Metrics] = None, service_name: str = "cogency"):
        from .metrics import get_metrics

        self.metrics = metrics or get_metrics()
        self.service_name = service_name

    def export(self) -> Dict:
        """Export all metrics as OpenTelemetry JSON format."""
        timestamp_ns = int(time.time() * 1_000_000_000)

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
                    "metrics": self._export_metrics(timestamp_ns),
                }
            ],
        }

        return {"resourceMetrics": [resource_metrics]}

    def _export_metrics(self, timestamp_ns: int) -> List[Dict]:
        """Export all metric types."""
        metrics = []

        # Export counters as sums
        for key, value in self.metrics.counters.items():
            name, tags = self._parse_key(key)
            metrics.append(
                {
                    "name": f"cogency.{name}",
                    "description": f"Cogency {name} counter",
                    "unit": "1",
                    "sum": {
                        "dataPoints": [
                            {
                                "attributes": self._format_attributes(tags),
                                "timeUnixNano": timestamp_ns,
                                "asDouble": float(value),
                                "isMonotonic": True,
                            }
                        ],
                        "aggregationTemporality": 2,  # CUMULATIVE
                    },
                }
            )

        # Export gauges
        for key, value in self.metrics.gauges.items():
            name, tags = self._parse_key(key)
            metrics.append(
                {
                    "name": f"cogency.{name}",
                    "description": f"Cogency {name} gauge",
                    "unit": "1",
                    "gauge": {
                        "dataPoints": [
                            {
                                "attributes": self._format_attributes(tags),
                                "timeUnixNano": timestamp_ns,
                                "asDouble": float(value),
                            }
                        ]
                    },
                }
            )

        # Export histograms
        for summary in self.metrics.all_summaries():
            metrics.append(
                {
                    "name": f"cogency.{summary.name}",
                    "description": f"Cogency {summary.name} histogram",
                    "unit": "s",
                    "histogram": {
                        "dataPoints": [
                            {
                                "attributes": self._format_attributes(summary.tags),
                                "timeUnixNano": timestamp_ns,
                                "count": str(summary.count),
                                "sum": summary.sum,
                                "bucketCounts": [
                                    str(int(summary.count * 0.5)),
                                    str(int(summary.count * 0.95)),
                                    str(int(summary.count * 0.99)),
                                    str(summary.count),
                                ],
                                "explicitBounds": [0.5, 0.95, 0.99],
                            }
                        ],
                        "aggregationTemporality": 2,  # CUMULATIVE
                    },
                }
            )

        return metrics

    def _parse_key(self, key: str) -> tuple:
        """Parse metric key into name and tags."""
        return self.metrics._parse(key)

    def _format_attributes(self, tags: Dict[str, str]) -> List[Dict]:
        """Format tags as OpenTelemetry attributes."""
        return [{"key": k, "value": {"stringValue": v}} for k, v in sorted(tags.items())]

    def export_json(self) -> str:
        """Export as JSON string."""
        return json.dumps(self.export(), indent=2)
