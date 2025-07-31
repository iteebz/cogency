"""Clean timing utilities."""

from time import perf_counter


def timer(label: str):
    """Beautiful timing closure - no ceremony, self-documenting."""
    start = perf_counter()

    def stop():
        duration = perf_counter() - start
        print(f"[timing] {label}: {duration:.2f}s")
        return duration

    return stop
