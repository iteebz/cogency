"""Core monitoring types and data structures."""
import time
from typing import Dict, Any
from dataclasses import dataclass
from enum import Enum


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
