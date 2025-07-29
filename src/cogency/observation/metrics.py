"""Production metrics collection and monitoring."""

import asyncio
import json
import logging
import statistics
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

DEFAULT_MAX_METRIC_POINTS = 10000


@dataclass
class MetricPoint:
    name: str
    value: float
    tags: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class MetricsSummary:
    name: str
    count: int
    sum: float
    min: float
    max: float
    avg: float
    p50: float
    p95: float
    p99: float
    tags: Dict[str, str] = field(default_factory=dict)


class Metrics:
    """High-performance metrics collector."""

    def __init__(self, max_points: int = DEFAULT_MAX_METRIC_POINTS):
        self.max_points = max_points
        self.points: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_points))
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.lock = threading.RLock()
        self.logger = logging.getLogger("metrics")

    def counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment counter metric."""
        key = self._key(name, tags or {})
        with self.lock:
            self.counters[key] += value

    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set gauge metric."""
        key = self._key(name, tags or {})
        with self.lock:
            self.gauges[key] = value

    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Record histogram value."""
        point = MetricPoint(name, value, tags or {})
        key = self._key(name, tags or {})
        with self.lock:
            self.points[key].append(point)

    def timer(self, name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        return TimerContext(self, name, tags or {})

    def get_summary(
        self, name: str, tags: Optional[Dict[str, str]] = None
    ) -> Optional[MetricsSummary]:
        """Get statistical summary of histogram data."""
        key = self._key(name, tags or {})
        with self.lock:
            if key not in self.points or not self.points[key]:
                return None

            values = [p.value for p in self.points[key]]
            if not values:
                return None

            return MetricsSummary(
                name=name,
                count=len(values),
                sum=sum(values),
                min=min(values),
                max=max(values),
                avg=statistics.mean(values),
                p50=statistics.median(values),
                p95=self._pct(values, 0.95),
                p99=self._pct(values, 0.99),
                tags=tags or {},
            )

    def all_summaries(self) -> List[MetricsSummary]:
        """Get summaries for all metrics."""
        summaries = []
        with self.lock:
            processed_keys = set()
            for key in self.points:
                if key in processed_keys:
                    continue

                name, tags = self._parse(key)
                summary = self.get_summary(name, tags)
                if summary:
                    summaries.append(summary)
                    processed_keys.add(key)

        return summaries

    def reset(self):
        """Reset all metrics."""
        with self.lock:
            self.points.clear()
            self.counters.clear()
            self.gauges.clear()

    def to_dict(self) -> Dict[str, Any]:
        """Export metrics as dictionary."""
        with self.lock:
            return {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {k: [p.value for p in v] for k, v in self.points.items()},
            }

    def _key(self, name: str, tags: Dict[str, str]) -> str:
        """Create unique key for metric."""
        if not tags:
            return name
        tag_str = ",".join(f"{k}={v}" for k, v in sorted(tags.items()))
        return f"{name}#{tag_str}"

    def _parse(self, key: str) -> tuple:
        """Parse key back to name and tags."""
        if "#" not in key:
            return key, {}

        name, tag_str = key.split("#", 1)
        tags = {}
        if tag_str:
            for pair in tag_str.split(","):
                tag_key, tag_value = pair.split("=", 1)
                tags[tag_key] = tag_value
        return name, tags

    def _pct(self, values: List[float], p: float) -> float:
        """Calculate percentile."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = (len(sorted_values) - 1) * p
        floor_index = int(index)
        fractional_part = index - floor_index

        if floor_index + 1 < len(sorted_values):
            return (
                sorted_values[floor_index] * (1 - fractional_part)
                + sorted_values[floor_index + 1] * fractional_part
            )
        else:
            return sorted_values[floor_index]


class TimerContext:
    """Timer context manager."""

    def __init__(self, collector: Metrics, name: str, tags: Dict[str, str]):
        self.collector = collector
        self.name = name
        self.tags = tags
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.collector.histogram(self.name, duration, self.tags)


class MetricsReporter:
    """Report metrics to various backends."""

    def __init__(self, collector: Metrics):
        self.collector = collector
        self.logger = logging.getLogger("metrics.reporter")

    def log_summary(self):
        """Log metrics summary."""
        summaries = self.collector.all_summaries()
        if not summaries:
            return

        self.logger.info("=== METRICS SUMMARY ===")
        for summary in summaries:
            self.logger.info(
                f"{summary.name}: count={summary.count}, "
                f"avg={summary.avg:.3f}, p95={summary.p95:.3f}, p99={summary.p99:.3f}"
            )

    def to_json(self, filepath: str):
        """Export metrics to JSON file."""
        data = {
            "timestamp": time.time(),
            "summaries": [
                {
                    "name": s.name,
                    "count": s.count,
                    "sum": s.sum,
                    "min": s.min,
                    "max": s.max,
                    "avg": s.avg,
                    "p50": s.p50,
                    "p95": s.p95,
                    "p99": s.p99,
                    "tags": s.tags,
                }
                for s in self.collector.all_summaries()
            ],
            "raw": self.collector.to_dict(),
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

    async def start_reporting(self, interval: float = 60.0) -> None:
        """Start background metrics reporting."""
        while True:
            try:
                self.log_summary()
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Metrics reporting error: {e}")
                await asyncio.sleep(interval)


_metrics = Metrics()


def get_metrics() -> Metrics:
    """Get global metrics collector."""
    return _metrics


def counter(name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
    """Record counter metric."""
    _metrics.counter(name, value, tags)


def gauge(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Record gauge metric."""
    _metrics.gauge(name, value, tags)


def histogram(name: str, value: float, tags: Optional[Dict[str, str]] = None):
    """Record histogram metric."""
    _metrics.histogram(name, value, tags)


def timer(name: str, tags: Optional[Dict[str, str]] = None):
    """Timer context manager."""
    return _metrics.timer(name, tags)


def measure(metric_name: str, tags: Optional[Dict[str, str]] = None):
    """Decorator to automatically time function execution."""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs) -> Any:
                with timer(metric_name, tags):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                with timer(metric_name, tags):
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator
