"""Lightweight benchmarking system for phase-level performance analysis."""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..observe.profiling import get_profiler

SCHEMA_VERSION = "1.0"


def _extract_peak_memory(profiler_summary: Dict) -> float:
    """Extract peak memory usage from profiler summary."""
    if not profiler_summary or "operations" not in profiler_summary:
        return 0.0

    peak = 0.0
    for op_data in profiler_summary["operations"].values():
        if "peak_memory" in op_data:
            peak = max(peak, op_data["peak_memory"])

    return peak


def _extract_avg_cpu(profiler_summary: Dict) -> float:
    """Extract average CPU usage from profiler summary."""
    if not profiler_summary or "operations" not in profiler_summary:
        return 0.0

    total_cpu = 0.0
    count = 0
    for op_data in profiler_summary["operations"].values():
        if "avg_cpu_percent" in op_data:
            total_cpu += op_data["avg_cpu_percent"]
            count += 1

    return total_cpu / count if count > 0 else 0.0


def normalize_benchmark_report(
    eval_name: str, benchmark_data: Dict, profiler_summary: Dict, timestamp: float = None
) -> Dict:
    """Normalize benchmark data into stable schema."""
    return {
        "schema_version": SCHEMA_VERSION,
        "eval_name": eval_name,
        "total_duration": benchmark_data.get("total_duration", 0.0),
        "phase_timings": benchmark_data.get("phase_timings", {}),
        "timestamp": timestamp or time.perf_counter(),
        "memory_peak": _extract_peak_memory(profiler_summary),
        "cpu_percent": _extract_avg_cpu(profiler_summary),
        "system_metrics": profiler_summary,
    }


def validate_schema(report: Dict) -> bool:
    """Validate benchmark report schema."""
    required_fields = {
        "schema_version",
        "eval_name",
        "total_duration",
        "phase_timings",
        "timestamp",
        "memory_peak",
        "cpu_percent",
    }

    return all(field in report for field in required_fields)


@dataclass
class PhaseBenchmark:
    """Phase execution timing and metadata."""

    phase: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    metadata: Dict = field(default_factory=dict)

    def complete(self, metadata: Optional[Dict] = None) -> None:
        """Mark phase as complete and calculate duration."""
        self.end_time = time.perf_counter()
        self.duration = self.end_time - self.start_time
        if metadata:
            self.metadata.update(metadata)


@dataclass
class EvalBenchmark:
    """Complete evaluation benchmark with phase breakdowns."""

    eval_name: str
    start_time: float
    phases: List[PhaseBenchmark] = field(default_factory=list)
    total_duration: Optional[float] = None

    def add_phase(self, phase: str, metadata: Optional[Dict] = None) -> PhaseBenchmark:
        """Start timing a new phase."""
        benchmark = PhaseBenchmark(
            phase=phase, start_time=time.perf_counter(), metadata=metadata or {}
        )
        self.phases.append(benchmark)
        return benchmark

    def complete(self) -> None:
        """Complete the eval benchmark."""
        end_time = time.perf_counter()
        self.total_duration = end_time - self.start_time

        # Complete any uncompleted phases
        for phase in self.phases:
            if phase.duration is None:
                phase.complete()


class BenchmarkNotifier:
    """Notifier wrapper that captures phase timing automatically."""

    def __init__(self, wrapped_notifier=None):
        self.wrapped = wrapped_notifier
        self.current_benchmark: Optional[EvalBenchmark] = None
        self.current_phase: Optional[PhaseBenchmark] = None

    def start_eval(self, eval_name: str) -> EvalBenchmark:
        """Start benchmarking an evaluation."""
        self.current_benchmark = EvalBenchmark(eval_name=eval_name, start_time=time.perf_counter())
        return self.current_benchmark

    def __call__(self, notification):
        """Handle notification and capture timing (sync callback for notification system)."""
        event_type = notification.type
        payload = notification.data

        # Capture phase transitions
        if event_type in ["preprocess", "reason", "act", "respond"]:
            state = payload.get("state", "unknown")

            if state == "generating" or state == "starting":
                # Complete previous phase if exists
                if self.current_phase and self.current_phase.duration is None:
                    self.current_phase.complete()

                # Start new phase
                if self.current_benchmark:
                    self.current_phase = self.current_benchmark.add_phase(
                        event_type, {"state": state, **payload}
                    )

            elif state == "complete" and self.current_phase:
                # Complete current phase
                self.current_phase.complete(payload)

        # Forward to wrapped notifier
        if self.wrapped:
            self.wrapped(notification)

    def get_report(self) -> Optional[Dict]:
        """Get normalized benchmark report for current eval."""
        if not self.current_benchmark:
            return None

        # Ensure benchmark is complete
        self.current_benchmark.complete()

        # Normalize phase timings into consistent structure
        phase_timings = {}
        for phase in self.current_benchmark.phases:
            phase_timings[phase.phase] = phase.duration or 0.0

        return {
            "schema_version": SCHEMA_VERSION,
            "eval_name": self.current_benchmark.eval_name,
            "total_duration": self.current_benchmark.total_duration or 0.0,
            "phase_timings": phase_timings,
            "timestamp": self.current_benchmark.start_time,
        }


async def benchmark_eval(eval_instance, original_notifier=None) -> Dict:
    """Benchmark a single evaluation with phase-level timing."""
    bench_notifier = BenchmarkNotifier(original_notifier)
    bench_notifier.start_eval(eval_instance.name)

    # Monkey patch the eval to use benchmarking
    original_run = eval_instance.run

    async def benchmarked_run():
        """Run the eval with benchmark notifier injection."""
        # Inject benchmark notifier into any Agent creation
        import cogency

        original_agent_init = cogency.Agent.__init__

        def patched_init(self, *args, **kwargs):
            # Inject our benchmark notifier
            kwargs["on_notify"] = bench_notifier
            return original_agent_init(self, *args, **kwargs)

        cogency.Agent.__init__ = patched_init

        try:
            result = await original_run()
            return result
        finally:
            # Restore original
            cogency.Agent.__init__ = original_agent_init

    # Use profiler for system-level metrics
    profiler = get_profiler()

    async with profiler.profile(f"eval_{eval_instance.name}"):
        # Execute the eval with patched Agent
        eval_instance.run = benchmarked_run
        result = await eval_instance.execute()
        eval_instance.run = original_run  # Restore

    # Get both benchmark and profiler data
    benchmark_report = bench_notifier.get_report()
    profiler_summary = profiler.summary()

    # Normalize into stable schema
    if benchmark_report:
        normalized_report = normalize_benchmark_report(
            benchmark_report["eval_name"],
            benchmark_report,
            profiler_summary,
            benchmark_report["timestamp"],
        )
    else:
        normalized_report = normalize_benchmark_report(eval_instance.name, {}, profiler_summary)

    return {
        "benchmark_report": normalized_report,
        "eval_result": result.unwrap() if result.is_ok() else None,
    }
