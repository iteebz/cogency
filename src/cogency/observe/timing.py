"""Pure timing utilities - stdlib time.perf_counter() instrumentation."""

import time
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def timer(label: str) -> Generator[tuple[str, float], None, None]:
    """Timer context manager for measuring duration - pure instrumentation.

    Returns:
        tuple[str, float]: (label, start_time) for caller coordination
    """
    start = time.perf_counter()
    try:
        yield (label, start)
    finally:
        time.perf_counter() - start
        # Pure instrumentation - caller handles timing data


def measure(func_name: str = None):
    """Simple function timing decorator - returns timing data."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            name = func_name or f"{func.__module__}.{func.__name__}"
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                duration = time.perf_counter() - start
                # Store timing for potential emission elsewhere
                wrapper._last_timing = (name, duration)

        return wrapper

    return decorator
