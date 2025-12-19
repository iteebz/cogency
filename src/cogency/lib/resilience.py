import asyncio
import inspect
from collections.abc import Awaitable, Callable
from functools import wraps
from typing import ParamSpec, TypeVar, cast

P = ParamSpec("P")
T = TypeVar("T")


def retry(attempts: int = 3, base_delay: float = 0.1) -> Callable[[Callable[P, T]], Callable[P, T]]:  # noqa: C901  # dual sync/async decorator
    """Retry decorator with exponential backoff. Works with sync and async functions."""

    def decorator(func: Callable[P, T]) -> Callable[P, T]:  # handles both coroutine and regular functions
        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                last_exc: Exception | None = None
                for attempt in range(attempts):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        last_exc = e
                        if attempt < attempts - 1:
                            delay = base_delay * (2**attempt)
                            await asyncio.sleep(delay)

                raise last_exc  # type: ignore[misc]  # last_exc always set when loop completes

            return cast("Callable[P, T]", async_wrapper)

        @wraps(func)
        def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
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

            raise last_exc  # type: ignore[misc]  # last_exc always set when loop completes

        return sync_wrapper

    return decorator


def timeout(seconds: float = 30) -> Callable[[Callable[P, Awaitable[T]]], Callable[P, Awaitable[T]]]:
    def decorator(func: Callable[P, Awaitable[T]]) -> Callable[P, Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)

        return wrapper

    return decorator
