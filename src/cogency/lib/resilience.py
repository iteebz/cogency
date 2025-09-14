"""Resilient operations - ripped from resilient-result, simplified."""

import asyncio
from functools import wraps


def retry(attempts: int = 3, base_delay: float = 0.1):
    """Simple retry decorator with exponential backoff - no Result ceremony."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    result = (
                        await func(*args, **kwargs)
                        if asyncio.iscoroutinefunction(func)
                        else func(*args, **kwargs)
                    )

                    # For functions that return False on failure, treat as exception
                    if result is False:
                        raise RuntimeError("Operation returned False")

                    return result

                except Exception:
                    # If this is the last attempt, don't sleep or retry
                    if attempt < attempts - 1:
                        delay = base_delay * (2**attempt)
                        await asyncio.sleep(delay)

            # All attempts failed - return False for graceful degradation
            return False

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
