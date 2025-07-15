"""Production monitoring and observability for cogency framework."""
import time
import json
import asyncio
from typing import Dict, Any, Optional, List, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from enum import Enum
from contextlib import asynccontextmanager
from collections import defaultdict, deque
import threading
import logging


class MetricType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Metric:
    """Represents a single metric measurement."""
    name: str
    value: float
    metric_type: MetricType
    timestamp: float
    tags: Dict[str, str]
    labels: Dict[str, str]


@dataclass
class Alert:
    """Represents an alert condition."""
    name: str
    level: AlertLevel
    message: str
    timestamp: float
    metric_name: str
    threshold: float
    current_value: float
    metadata: Dict[str, Any]


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
    
    def get_metrics_snapshot(self) -> Dict[str, Any]:
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


class AlertManager:
    """Manages alerts and thresholds for cogency operations."""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.thresholds: Dict[str, Dict[str, float]] = {}
        self.alert_handlers: List[Callable[[Alert], None]] = []
        self._lock = threading.Lock()
    
    def add_threshold(self, metric_name: str, level: AlertLevel, threshold: float):
        """Add an alert threshold."""
        with self._lock:
            if metric_name not in self.thresholds:
                self.thresholds[metric_name] = {}
            self.thresholds[metric_name][level.value] = threshold
    
    def add_alert_handler(self, handler: Callable[[Alert], None]):
        """Add an alert handler function."""
        self.alert_handlers.append(handler)
    
    def check_thresholds(self, metrics: Dict[str, Any]):
        """Check metrics against thresholds and trigger alerts."""
        with self._lock:
            for metric_name, thresholds in self.thresholds.items():
                current_value = self._get_metric_value(metric_name, metrics)
                
                if current_value is None:
                    continue
                
                for level_str, threshold in thresholds.items():
                    level = AlertLevel(level_str)
                    
                    if self._threshold_exceeded(current_value, threshold, level):
                        alert = Alert(
                            name=f"{metric_name}_threshold_{level.value}",
                            level=level,
                            message=f"Metric {metric_name} exceeded {level.value} threshold: {current_value} > {threshold}",
                            timestamp=time.time(),
                            metric_name=metric_name,
                            threshold=threshold,
                            current_value=current_value,
                            metadata={"metric_snapshot": metrics}
                        )
                        
                        self.alerts.append(alert)
                        
                        # Trigger alert handlers
                        for handler in self.alert_handlers:
                            try:
                                handler(alert)
                            except Exception as e:
                                logging.error(f"Alert handler failed: {e}")
    
    def _get_metric_value(self, metric_name: str, metrics: Dict[str, Any]) -> Optional[float]:
        """Extract metric value from metrics snapshot."""
        # Check counters
        if metric_name in metrics.get("counters", {}):
            return metrics["counters"][metric_name]
        
        # Check gauges
        if metric_name in metrics.get("gauges", {}):
            return metrics["gauges"][metric_name]
        
        # Check histogram averages
        if metric_name in metrics.get("histograms", {}):
            return metrics["histograms"][metric_name].get("mean", 0.0)
        
        # Check timer averages
        if metric_name in metrics.get("timers", {}):
            return metrics["timers"][metric_name].get("avg_duration", 0.0)
        
        return None
    
    def _threshold_exceeded(self, current_value: float, threshold: float, level: AlertLevel) -> bool:
        """Check if threshold is exceeded based on alert level."""
        if level in [AlertLevel.ERROR, AlertLevel.CRITICAL]:
            return current_value > threshold
        elif level == AlertLevel.WARNING:
            return current_value > threshold * 0.8  # 80% of threshold
        else:
            return current_value > threshold * 0.6  # 60% of threshold


class CogencyMonitor:
    """Main monitoring class for cogency framework."""
    
    def __init__(self, export_path: Optional[str] = None):
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self.export_path = Path(export_path) if export_path else Path("monitoring")
        self.export_path.mkdir(exist_ok=True)
        self._monitoring_active = False
        self._monitoring_task = None
        
        # Setup default thresholds
        self._setup_default_thresholds()
        
        # Setup default alert handlers
        self._setup_default_alert_handlers()
    
    def _setup_default_thresholds(self):
        """Setup default alert thresholds for cogency operations."""
        # Reasoning performance thresholds
        self.alerts.add_threshold("reasoning_loop_duration", AlertLevel.WARNING, 5.0)
        self.alerts.add_threshold("reasoning_loop_duration", AlertLevel.ERROR, 10.0)
        self.alerts.add_threshold("reasoning_loop_duration", AlertLevel.CRITICAL, 30.0)
        
        # Tool execution thresholds
        self.alerts.add_threshold("tool_execution_duration", AlertLevel.WARNING, 2.0)
        self.alerts.add_threshold("tool_execution_duration", AlertLevel.ERROR, 5.0)
        
        # Memory access thresholds
        self.alerts.add_threshold("memory_access_duration", AlertLevel.WARNING, 1.0)
        self.alerts.add_threshold("memory_access_duration", AlertLevel.ERROR, 3.0)
        
        # Failure rate thresholds
        self.alerts.add_threshold("tool_failure_rate", AlertLevel.WARNING, 0.1)
        self.alerts.add_threshold("tool_failure_rate", AlertLevel.ERROR, 0.2)
        self.alerts.add_threshold("tool_failure_rate", AlertLevel.CRITICAL, 0.5)
    
    def _setup_default_alert_handlers(self):
        """Setup default alert handlers."""
        def log_alert(alert: Alert):
            log_level = {
                AlertLevel.INFO: logging.info,
                AlertLevel.WARNING: logging.warning,
                AlertLevel.ERROR: logging.error,
                AlertLevel.CRITICAL: logging.critical
            }
            log_level[alert.level](f"ALERT: {alert.message}")
        
        def export_alert(alert: Alert):
            alert_file = self.export_path / "alerts.jsonl"
            with open(alert_file, "a") as f:
                f.write(json.dumps(asdict(alert)) + "\n")
        
        self.alerts.add_alert_handler(log_alert)
        self.alerts.add_alert_handler(export_alert)
    
    @asynccontextmanager
    async def monitor_operation(self, operation_name: str, tags: Optional[Dict[str, str]] = None):
        """Context manager for monitoring an operation."""
        start_time = time.time()
        
        try:
            yield self
        except Exception as e:
            self.metrics.counter(f"{operation_name}_failures", tags=tags)
            raise
        finally:
            duration = time.time() - start_time
            self.metrics.timer(f"{operation_name}_duration", duration, tags=tags)
            self.metrics.counter(f"{operation_name}_calls", tags=tags)
    
    def start_monitoring(self, interval: float = 60.0):
        """Start background monitoring and alerting."""
        if self._monitoring_active:
            return
        
        self._monitoring_active = True
        self._monitoring_task = asyncio.create_task(self._monitoring_loop(interval))
    
    async def stop_monitoring(self):
        """Stop background monitoring."""
        self._monitoring_active = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self, interval: float):
        """Background monitoring loop."""
        while self._monitoring_active:
            try:
                # Get metrics snapshot
                metrics = self.metrics.get_metrics_snapshot()
                
                # Check thresholds
                self.alerts.check_thresholds(metrics)
                
                # Export metrics
                await self._export_metrics(metrics)
                
                # Calculate failure rates
                self._calculate_failure_rates(metrics)
                
                await asyncio.sleep(interval)
                
            except Exception as e:
                logging.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(interval)
    
    async def _export_metrics(self, metrics: Dict[str, Any]):
        """Export metrics to files."""
        timestamp = datetime.now().isoformat()
        
        # Export JSON metrics
        metrics_file = self.export_path / f"metrics_{timestamp}.json"
        with open(metrics_file, "w") as f:
            json.dump(metrics, f, indent=2)
        
        # Export Prometheus format
        prometheus_file = self.export_path / "metrics.prom"
        with open(prometheus_file, "w") as f:
            f.write(self._format_prometheus_metrics(metrics))
    
    def _format_prometheus_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics in Prometheus format."""
        output = []
        
        # Counters
        for name, value in metrics.get("counters", {}).items():
            output.append(f"# TYPE {name} counter")
            output.append(f"{name} {value}")
        
        # Gauges
        for name, value in metrics.get("gauges", {}).items():
            output.append(f"# TYPE {name} gauge")
            output.append(f"{name} {value}")
        
        # Histograms
        for name, stats in metrics.get("histograms", {}).items():
            output.append(f"# TYPE {name} histogram")
            output.append(f"{name}_count {stats['count']}")
            output.append(f"{name}_sum {stats['sum']}")
            output.append(f"{name}_bucket{{le=\"0.5\"}} {stats['p50']}")
            output.append(f"{name}_bucket{{le=\"0.95\"}} {stats['p95']}")
            output.append(f"{name}_bucket{{le=\"0.99\"}} {stats['p99']}")
        
        return "\n".join(output)
    
    def _calculate_failure_rates(self, metrics: Dict[str, Any]):
        """Calculate and record failure rates."""
        for metric_name, count in metrics.get("counters", {}).items():
            if metric_name.endswith("_failures"):
                base_name = metric_name[:-9]  # Remove "_failures"
                total_calls = metrics.get("counters", {}).get(f"{base_name}_calls", 0)
                
                if total_calls > 0:
                    failure_rate = count / total_calls
                    self.metrics.gauge(f"{base_name}_failure_rate", failure_rate)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        metrics = self.metrics.get_metrics_snapshot()
        recent_alerts = [a for a in self.alerts.alerts if time.time() - a.timestamp < 300]  # Last 5 minutes
        
        # Determine overall health
        critical_alerts = [a for a in recent_alerts if a.level == AlertLevel.CRITICAL]
        error_alerts = [a for a in recent_alerts if a.level == AlertLevel.ERROR]
        warning_alerts = [a for a in recent_alerts if a.level == AlertLevel.WARNING]
        
        if critical_alerts:
            status = "CRITICAL"
        elif error_alerts:
            status = "ERROR"
        elif warning_alerts:
            status = "WARNING"
        else:
            status = "HEALTHY"
        
        return {
            "status": status,
            "timestamp": time.time(),
            "metrics_summary": {
                "total_counters": len(metrics.get("counters", {})),
                "total_gauges": len(metrics.get("gauges", {})),
                "total_histograms": len(metrics.get("histograms", {})),
                "total_timers": len(metrics.get("timers", {}))
            },
            "alerts_summary": {
                "total_alerts": len(recent_alerts),
                "critical": len(critical_alerts),
                "error": len(error_alerts),
                "warning": len(warning_alerts)
            }
        }


# Global monitor instance
_monitor = CogencyMonitor()


def get_monitor() -> CogencyMonitor:
    """Get the global monitor instance."""
    return _monitor