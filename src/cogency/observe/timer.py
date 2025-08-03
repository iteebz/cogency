"""Timing utilities."""

from time import perf_counter


def timer(label: str):
    """Timing closure."""
    start = perf_counter()

    def stop():
        duration = perf_counter() - start
        # Timing info - could use notifier if timing events needed
        return duration

    return stop
