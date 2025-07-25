"""Circuit breaker for runaway protection."""

import time
from collections import defaultdict
from functools import wraps
from typing import Dict


class CircuitBreaker:
    """Minimal circuit breaker for runaway protection."""

    def __init__(self):
        self._failures: Dict[str, list] = defaultdict(list)

    def is_open(self, func_name: str, failures: int, window: int) -> bool:
        """Check if circuit is open (too many failures)."""
        now = time.time()
        fails = self._failures[func_name]

        # Remove old failures outside time window
        self._failures[func_name] = [f for f in fails if now - f < window]

        return len(self._failures[func_name]) >= failures

    def record_failure(self, func_name: str) -> None:
        """Record a failure for this function."""
        self._failures[func_name].append(time.time())


# Global instance
circuit_breaker = CircuitBreaker()


def circuit(failures: int = 3, window: int = 300):
    """Circuit breaker for runaway protection."""

    def decorator(func):
        func_name = f"{func.__module__}.{func.__qualname__}"

        @wraps(func)
        async def circuit_protected(*args, **kwargs):
            # Check if circuit is open
            if circuit_breaker.is_open(func_name, failures, window):
                return f"Circuit breaker open for {func_name} - too many failures"

            try:
                return await func(*args, **kwargs)
            except Exception:
                # Record failure and re-raise
                circuit_breaker.record_failure(func_name)
                raise

        return circuit_protected

    return decorator
