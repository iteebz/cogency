"""Observability and metrics for agent monitoring.

This module provides comprehensive observability capabilities:

- Profiler: Performance profiling utilities
- profile_async, profile_sync: Profiling decorators
- Prometheus, OpenTelemetry: Metrics exporters
- cost, count: Token usage analysis

Internal metrics APIs are accessed via Agent observe=True configuration rather
than direct import to maintain clean separation of concerns.
"""

from .exporters import OpenTelemetry, Prometheus

# Internal metrics not exported - use Agent(observe=True) instead
# from .metrics import counter, gauge, histogram, timer, measure, etc.
from .profiling import Profiler, profile_async, profile_sync
from .tokens import cost, count

__all__ = [
    # Public observability APIs - accessed via Agent config
    "Profiler",
    "profile_async",
    "profile_sync",
    "Prometheus",
    "OpenTelemetry",
    "cost",  # Token cost estimation
    "count",  # Token counting
    # Internal metrics APIs not exported:
    # - counter, gauge, histogram, timer, measure (use Agent observe=True)
    # - MetricPoint, Metrics, MetricsReporter, etc. (implementation details)
]
