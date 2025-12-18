import asyncio
import inspect
from functools import wraps


def retry(attempts: int = 3, base_delay: float = 0.1):  # noqa: C901  # dual sync/async decorator
    """Retry decorator with exponential backoff. Works with sync and async functions."""

    def decorator(func):  # noqa: C901  # handles both coroutine and regular functions
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                last_exc: Exception | None = None
                for attempt in range(attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exc = e
                        if attempt < attempts - 1:
                            delay = base_delay * (2**attempt)
                            await asyncio.sleep(delay)

                if last_exc:
                    raise last_exc
                return None

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            import time

            last_exc: Exception | None = None
            for attempt in range(attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < attempts - 1:
                        delay = base_delay * (2**attempt)
                        time.sleep(delay)

            if last_exc:
                raise last_exc
            return None

        return sync_wrapper

    return decorator


def timeout(seconds: float = 30):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)

        return wrapper

    return decorator
