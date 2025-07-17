"""Metrics collection and aggregation."""
import time
import threading
from typing import Dict, List, Optional
from collections import defaultdict, deque

from .types import Metric, MetricType


class MetricsCollector:
    """Collects and aggregates metrics for cogency operations."""
    
    def __init__(self, buffer_size: int = 1000):
        self.metrics: deque = deque(maxlen=buffer_size)
        self.counters: Dict[str, float] = defaultdict(float)
        self.gauges: Dict[str, float] = {}
        self.histograms: Dict[str, List[float]] = defaultdict(list)
        self.timers: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()
        
    def counter(self, name: str, value: float = 1.0, tags: Optional[Dict[str, str]] = None):
        """Increment a counter metric."""
        with self._lock:
            self.counters[name] += value
            metric = Metric(
                name=name,
                value=self.counters[name],
                metric_type=MetricType.COUNTER,
                timestamp=time.time(),
                tags=tags or {},
                labels={}
            )
            self.metrics.append(metric)
    
    def gauge(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Set a gauge metric."""
        with self._lock:
            self.gauges[name] = value
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.GAUGE,
                timestamp=time.time(),
                tags=tags or {},
                labels={}
            )
            self.metrics.append(metric)
    
    def histogram(self, name: str, value: float, tags: Optional[Dict[str, str]] = None):
        """Add a value to a histogram."""
        with self._lock:
            self.histograms[name].append(value)
            metric = Metric(
                name=name,
                value=value,
                metric_type=MetricType.HISTOGRAM,
                timestamp=time.time(),
                tags=tags or {},
                labels={}
            )
            self.metrics.append(metric)
    
    def timer(self, name: str, duration: float, tags: Optional[Dict[str, str]] = None):
        """Record a timer metric."""
        with self._lock:
            self.timers[name].append(duration)
            metric = Metric(
                name=name,
                value=duration,
                metric_type=MetricType.TIMER,
                timestamp=time.time(),
                tags=tags or {},
                labels={}
            )
            self.metrics.append(metric)
    
    def get_metrics_snapshot(self) -> Dict[str, any]:
        """Get current metrics snapshot."""
        with self._lock:
            snapshot = {
                "counters": dict(self.counters),
                "gauges": dict(self.gauges),
                "histograms": {},
                "timers": {},
                "timestamp": time.time()
            }
            
            # Calculate histogram statistics
            for name, values in self.histograms.items():
                if values:
                    snapshot["histograms"][name] = {
                        "count": len(values),
                        "sum": sum(values),
                        "mean": sum(values) / len(values),
                        "min": min(values),
                        "max": max(values),
                        "p50": self._percentile(values, 50),
                        "p95": self._percentile(values, 95),
                        "p99": self._percentile(values, 99)
                    }
            
            # Calculate timer statistics
            for name, durations in self.timers.items():
                if durations:
                    snapshot["timers"][name] = {
                        "count": len(durations),
                        "total_duration": sum(durations),
                        "avg_duration": sum(durations) / len(durations),
                        "min_duration": min(durations),
                        "max_duration": max(durations),
                        "p50": self._percentile(durations, 50),
                        "p95": self._percentile(durations, 95),
                        "p99": self._percentile(durations, 99)
                    }
            
            return snapshot
    
    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0
        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]
