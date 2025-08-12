"""Instrumentation domain - timing, metrics, profiling."""

from .decorators import observe
from .timing import timer

__all__ = ["timer", "observe"]
