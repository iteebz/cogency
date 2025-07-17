"""Alert management and threshold monitoring."""
import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any

from .types import Alert, AlertLevel


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
