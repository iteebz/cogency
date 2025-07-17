"""Main monitoring orchestrator for cogency framework."""
import time
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from contextlib import asynccontextmanager

from .types import AlertLevel
from .collector import MetricsCollector
from .alerts import AlertManager


class CogencyMonitor:
    """Main monitoring class for cogency framework."""
    
    def __init__(self, export_path: Optional[str] = None):
        self.metrics = MetricsCollector()
        self.alerts = AlertManager()
        self.export_path = Path(export_path) if export_path else Path(".cogency/monitoring")
        self.export_path.mkdir(parents=True, exist_ok=True)
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
        def log_alert(alert):
            log_level = {
                AlertLevel.INFO: logging.info,
                AlertLevel.WARNING: logging.warning,
                AlertLevel.ERROR: logging.error,
                AlertLevel.CRITICAL: logging.critical
            }
            log_level[alert.level](f"ALERT: {alert.message}")
        
        def export_alert(alert):
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
