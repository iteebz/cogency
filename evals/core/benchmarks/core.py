"""Lightweight benchmarking system for phase-level performance analysis."""

import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ...observe.profiling import get_profiler


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

    def add_step(self, phase: str, metadata: Optional[Dict] = None) -> PhaseBenchmark:
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
        self.current_step: Optional[PhaseBenchmark] = None

    def start_eval(self, eval_name: str) -> EvalBenchmark:
        """Start benchmarking an evaluation."""
        self.current_benchmark = EvalBenchmark(eval_name=eval_name, start_time=time.perf_counter())
        return self.current_benchmark

    def __call__(self, notification):
        """Handle notification and capture timing (sync callback for notification system)."""
        event_type = notification.type
        payload = notification.data

        # Capture phase transitions
        if event_type in ["prepare", "reason", "act", "respond"]:
            state = payload.get("state", "unknown")

            if state == "generating" or state == "starting":
                # Complete previous phase if exists
                if self.current_step and self.current_step.duration is None:
                    self.current_step.complete()

                # Start new phase
                if self.current_benchmark:
                    self.current_step = self.current_benchmark.add_step(
                        event_type, {"state": state, **payload}
                    )

            elif state == "complete" and self.current_step:
                # Complete current phase
                self.current_step.complete(payload)

        # Forward to wrapped notifier
        if self.wrapped:
            self.wrapped(notification)

    def get_report(self) -> Optional[Dict]:
        """Get benchmark report for current eval."""
        if not self.current_benchmark:
            return None

        # Ensure benchmark is complete
        self.current_benchmark.complete()

        report = {
            "eval_name": self.current_benchmark.eval_name,
            "total_duration": self.current_benchmark.total_duration,
            "phases": [],
        }

        for phase in self.current_benchmark.phases:
            report["phases"].append(
                {"phase": phase.phase, "duration": phase.duration, "metadata": phase.metadata}
            )

        return report


async def benchmark_eval(eval_instance, original_notifier=None) -> Dict:
    """Benchmark a single evaluation with phase-level timing."""
    benchmark_notifier = BenchmarkNotifier(original_notifier)
    benchmark_notifier.start_eval(eval_instance.name)

    # Monkey patch the eval to use benchmarking
    original_run = eval_instance.run

    async def benchmarked_run():
        """Run the eval with benchmark notifier injection."""
        # Inject benchmark notifier into any Agent creation
        import cogency

        original_agent_init = cogency.Agent.__init__

        def patched_init(self, *args, **kwargs):
            # Inject our benchmark notifier
            kwargs["on_notify"] = benchmark_notifier
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
    benchmark_report = benchmark_notifier.get_report()
    profiler_summary = profiler.summary()

    return {
        "phase_timing": benchmark_report,
        "system_metrics": profiler_summary,
        "eval_result": result.unwrap() if result.is_ok() else None,
    }
