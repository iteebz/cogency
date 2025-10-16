import asyncio
from functools import wraps


def retry(attempts: int = 3, base_delay: float = 0.1):
    """Retry decorator with exponential backoff. Raises exception on final failure."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(attempts):
                try:
                    return (
                        await func(*args, **kwargs)
                        if asyncio.iscoroutinefunction(func)
                        else func(*args, **kwargs)
                    )
                except Exception as e:
                    last_exc = e
                    if attempt < attempts - 1:
                        delay = base_delay * (2**attempt)
                        await asyncio.sleep(delay)

            raise last_exc

        return wrapper

    return decorator


def timeout(seconds: float = 30):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError as e:
                raise TimeoutError(f"Operation timed out after {seconds}s") from e

        return wrapper

    return decorator


class CircuitBreaker:
    """Tracks consecutive failures and forces termination after threshold."""

    def __init__(self, max_failures: int = 3):
        self.max_failures = max_failures
        self.consecutive_failures = 0

    def record_success(self):
        """Reset failure counter on success."""
        self.consecutive_failures = 0

    def record_failure(self) -> bool:
        """Record failure. Returns True if circuit should break."""
        self.consecutive_failures += 1
        return self.consecutive_failures >= self.max_failures

    def is_open(self) -> bool:
        """Check if circuit is open (should stop execution)."""
        return self.consecutive_failures >= self.max_failures
