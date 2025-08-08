"""Simple timing utilities - pure event emission."""

import time


class TimerContext:
    """Timer context manager - emits timing events only."""

    def __init__(self, label: str):
        self.label = label
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            from cogency.events import emit

            emit("timing", label=self.label, duration=duration)

    @property
    def current_elapsed(self) -> float:
        """Get current elapsed time (live during execution)."""
        if self.start_time:
            return time.time() - self.start_time
        return 0.0


def timer(label: str):
    """Timer context manager for measuring duration."""
    return TimerContext(label)
