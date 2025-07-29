"""System profiling utilities for performance bottleneck detection."""

import asyncio
import json
import threading
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncContextManager, Callable, Dict, List, Optional

import psutil


@dataclass
class ProfileMetrics:
    """Performance metrics for a profiled operation."""

    operation_name: str
    start_time: float
    end_time: float
    duration: float
    memory_before: float
    memory_after: float
    memory_delta: float
    cpu_percent: float
    peak_memory: float
    metadata: Dict[str, Any]


class Profiler:
    """Production-grade system profiler for cognitive operations."""

    def __init__(self, sample_interval: float = 0.1):
        self.sample_interval = sample_interval
        self.metrics: List[ProfileMetrics] = []
        self.active_profiles: Dict[str, Dict[str, Any]] = {}
        self._monitoring_thread = None
        self._monitoring_stop = threading.Event()
        self._memory_samples = defaultdict(list)
        self._cpu_samples = defaultdict(list)

    @asynccontextmanager
    async def profile(
        self, operation_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncContextManager:
        """Context manager for profiling async operations."""
        start_time = time.time()
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB

        # Start monitoring
        self._start_monitoring(operation_name)

        try:
            yield self
        finally:
            # Stop monitoring
            self._stop_monitoring(operation_name)

            end_time = time.time()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            duration = end_time - start_time

            # Get peak memory and average CPU
            peak_memory = (
                max(self._memory_samples[operation_name])
                if self._memory_samples[operation_name]
                else memory_after
            )
            avg_cpu = (
                sum(self._cpu_samples[operation_name]) / len(self._cpu_samples[operation_name])
                if self._cpu_samples[operation_name]
                else 0
            )

            # Clean up samples
            del self._memory_samples[operation_name]
            del self._cpu_samples[operation_name]

            metric = ProfileMetrics(
                operation_name=operation_name,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
                memory_before=memory_before,
                memory_after=memory_after,
                memory_delta=memory_after - memory_before,
                cpu_percent=avg_cpu,
                peak_memory=peak_memory,
                metadata=metadata or {},
            )

            self.metrics.append(metric)

    def _start_monitoring(self, operation_name: str):
        """Start resource monitoring for operation."""
        self.active_profiles[operation_name] = {
            "start_time": time.time(),
            "monitoring": True,
        }

        def monitor():
            process = psutil.Process()
            while not self._monitoring_stop.is_set():
                if (
                    operation_name in self.active_profiles
                    and self.active_profiles[operation_name]["monitoring"]
                ):
                    try:
                        memory_mb = process.memory_info().rss / 1024 / 1024
                        cpu_percent = process.cpu_percent()

                        self._memory_samples[operation_name].append(memory_mb)
                        self._cpu_samples[operation_name].append(cpu_percent)
                    except (
                        psutil.NoSuchProcess,
                        psutil.AccessDenied,
                        psutil.ZombieProcess,
                    ):
                        pass  # Handle process termination gracefully

                time.sleep(self.sample_interval)

        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._monitoring_thread = threading.Thread(target=monitor, daemon=True)
            self._monitoring_thread.start()

    def _stop_monitoring(self, operation_name: str):
        """Stop monitoring for specific operation."""
        if operation_name in self.active_profiles:
            self.active_profiles[operation_name]["monitoring"] = False
            del self.active_profiles[operation_name]

    def get_bottlenecks(
        self, threshold_duration: float = 1.0, threshold_memory: float = 50.0
    ) -> List[ProfileMetrics]:
        """Identify performance bottlenecks based on thresholds."""
        bottlenecks = []

        for metric in self.metrics:
            is_bottleneck = (
                metric.duration > threshold_duration
                or metric.memory_delta > threshold_memory
                or metric.cpu_percent > 80
            )

            if is_bottleneck:
                bottlenecks.append(metric)

        return sorted(bottlenecks, key=lambda x: x.duration, reverse=True)

    def summary(self) -> Dict[str, Any]:
        """Generate performance summary report."""
        if not self.metrics:
            return {"message": "No profiling data available"}

        operations = defaultdict(list)
        for metric in self.metrics:
            operations[metric.operation_name].append(metric)

        summary = {
            "total_operations": len(self.metrics),
            "total_duration": sum(m.duration for m in self.metrics),
            "operations": {},
        }

        for op_name, op_metrics in operations.items():
            durations = [m.duration for m in op_metrics]
            memory_deltas = [m.memory_delta for m in op_metrics]

            summary["operations"][op_name] = {
                "count": len(op_metrics),
                "total_duration": sum(durations),
                "avg_duration": sum(durations) / len(durations),
                "max_duration": max(durations),
                "min_duration": min(durations),
                "avg_memory_delta": sum(memory_deltas) / len(memory_deltas),
                "max_memory_delta": max(memory_deltas),
                "peak_memory": max(m.peak_memory for m in op_metrics),
            }

        return summary

    def to_json(self, filepath: str):
        """Export detailed profiling report to JSON."""
        report = {
            "summary": self.summary(),
            "bottlenecks": [
                {
                    "operation": b.operation_name,
                    "duration": b.duration,
                    "memory_delta": b.memory_delta,
                    "cpu_percent": b.cpu_percent,
                    "peak_memory": b.peak_memory,
                    "metadata": b.metadata,
                }
                for b in self.get_bottlenecks()
            ],
            "detailed_metrics": [
                {
                    "operation": m.operation_name,
                    "duration": m.duration,
                    "memory_before": m.memory_before,
                    "memory_after": m.memory_after,
                    "memory_delta": m.memory_delta,
                    "cpu_percent": m.cpu_percent,
                    "peak_memory": m.peak_memory,
                    "start_time": m.start_time,
                    "end_time": m.end_time,
                    "metadata": m.metadata,
                }
                for m in self.metrics
            ],
        }

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2)


_profiler = Profiler()


def get_profiler() -> Profiler:
    """Get the global profiler instance."""
    return _profiler


async def profile_async(operation_name: str, func: Callable, *args, **kwargs) -> Any:
    """Profile an async operation with automatic context management."""
    async with _profiler.profile(operation_name, {"args": str(args), "kwargs": str(kwargs)}):
        return await func(*args, **kwargs)


def profile_sync(operation_name: str, func: Callable, *args, **kwargs):
    """Profile a sync operation with automatic context management."""

    async def wrapper() -> Any:
        async with _profiler.profile(operation_name, {"args": str(args), "kwargs": str(kwargs)}):
            return func(*args, **kwargs)

    return asyncio.run(wrapper())


class Profiler:
    """Specialized profiler for cogency framework operations."""

    def __init__(self):
        self.profiler = get_profiler()

    async def profile_reasoning_loop(self, func, *args, **kwargs) -> Any:
        """Profile the complete reasoning loop."""
        return await profile_async("reasoning_loop", func, *args, **kwargs)

    async def profile_tools(self, func, *args, **kwargs) -> Any:
        """Profile tool execution operations."""
        return await profile_async("tool_execution", func, *args, **kwargs)

    async def profile_memory(self, func, *args, **kwargs) -> Any:
        """Profile memory access operations."""
        return await profile_async("memory_access", func, *args, **kwargs)

    async def profile_llm(self, func, *args, **kwargs) -> Any:
        """Profile LLM inference operations."""
        return await profile_async("llm_inference", func, *args, **kwargs)

    def cogency_bottlenecks(self) -> Dict[str, List[ProfileMetrics]]:
        """Get bottlenecks categorized by cogency operations."""
        all_bottlenecks = self.profiler.bottlenecks()

        categorized = {
            "reasoning": [],
            "tool_execution": [],
            "memory_access": [],
            "llm_inference": [],
            "other": [],
        }

        for bottleneck in all_bottlenecks:
            if "reasoning" in bottleneck.operation_name:
                categorized["reasoning"].append(bottleneck)
            elif "tool_execution" in bottleneck.operation_name:
                categorized["tool_execution"].append(bottleneck)
            elif "memory_access" in bottleneck.operation_name:
                categorized["memory_access"].append(bottleneck)
            elif "llm_inference" in bottleneck.operation_name:
                categorized["llm_inference"].append(bottleneck)
            else:
                categorized["other"].append(bottleneck)

        return categorized
