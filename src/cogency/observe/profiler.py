"""System profiling with resource monitoring."""

import threading
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, AsyncContextManager, Dict, Optional

try:
    import psutil

    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False


class Profiler:
    """Advanced system profiling - pure event emission."""

    def __init__(self, sample_interval: float = 0.1):
        self.sample_interval = sample_interval
        self.active_profiles: Dict[str, Dict[str, Any]] = {}
        self._monitoring_thread = None
        self._monitoring_stop = threading.Event()
        self._memory_samples = defaultdict(list)
        self._cpu_samples = defaultdict(list)
        self.enabled = HAS_PSUTIL

    @asynccontextmanager
    async def profile(
        self, operation_name: str, metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncContextManager:
        """Context manager for profiling operations with system metrics."""
        start_time = time.time()
        memory_before = 0.0

        if self.enabled:
            try:
                process = psutil.Process()
                memory_before = process.memory_info().rss / 1024 / 1024  # MB
                self._start_monitoring(operation_name)
            except Exception:
                pass  # Fallback to basic timing

        try:
            yield self
        finally:
            end_time = time.time()
            duration = end_time - start_time
            memory_after = 0.0
            peak_memory = 0.0
            avg_cpu = 0.0

            if self.enabled:
                try:
                    self._stop_monitoring(operation_name)
                    process = psutil.Process()
                    memory_after = process.memory_info().rss / 1024 / 1024  # MB

                    # Get peak memory and average CPU
                    peak_memory = (
                        max(self._memory_samples[operation_name])
                        if self._memory_samples[operation_name]
                        else memory_after
                    )
                    avg_cpu = (
                        sum(self._cpu_samples[operation_name])
                        / len(self._cpu_samples[operation_name])
                        if self._cpu_samples[operation_name]
                        else 0
                    )

                    # Clean up samples
                    self._memory_samples.pop(operation_name, None)
                    self._cpu_samples.pop(operation_name, None)
                except Exception:
                    pass  # Fallback to basic metrics

            # Emit unified profiling event - no local storage
            from cogency.events import emit

            emit(
                "profile",
                operation=operation_name,
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

    def _start_monitoring(self, operation_name: str):
        """Start resource monitoring for operation."""
        if not self.enabled:
            return

        self.active_profiles[operation_name] = {
            "start_time": time.time(),
            "monitoring": True,
        }

        def monitor():
            try:
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
                        except Exception:
                            pass  # Handle process issues gracefully

                    time.sleep(self.sample_interval)
            except Exception:
                pass  # Thread cleanup

        if self._monitoring_thread is None or not self._monitoring_thread.is_alive():
            self._monitoring_thread = threading.Thread(target=monitor, daemon=True)
            self._monitoring_thread.start()

    def _stop_monitoring(self, operation_name: str):
        """Stop monitoring for specific operation."""
        if operation_name in self.active_profiles:
            self.active_profiles[operation_name]["monitoring"] = False
            del self.active_profiles[operation_name]


# Global instances
_profiler = Profiler()


def get_profiler() -> Profiler:
    """Get global profiler instance."""
    return _profiler


async def profile_async(operation_name: str, func, *args, **kwargs):
    """Profile an async operation."""
    async with _profiler.profile(operation_name, {"args": str(args), "kwargs": str(kwargs)}):
        return await func(*args, **kwargs)


def profile_sync(operation_name: str, func, *args, **kwargs):
    """Profile a sync operation with basic timing."""
    start_time = time.time()

    try:
        result = func(*args, **kwargs)
        return result
    finally:
        duration = time.time() - start_time
        from cogency.events import emit

        emit(
            "profile",
            operation=operation_name,
            start_time=start_time,
            end_time=time.time(),
            duration=duration,
            memory_before=0.0,
            memory_after=0.0,
            memory_delta=0.0,
            cpu_percent=0.0,
            peak_memory=0.0,
            metadata={"args": str(args), "kwargs": str(kwargs)},
        )
