"""The magical @resilient decorator - combines all resilience patterns."""

import functools
from typing import Optional, Any, Callable, TypeVar, Awaitable, Union

from .circuit import circuit
from .rate_limit import rate_limit
from ..utils.results import Result

T = TypeVar('T')


def resilient(
    rps: Optional[float] = None,
    burst: Optional[int] = None,
    failures: Optional[int] = None,
    window: Optional[int] = None,
    key: Optional[str] = None,
):
    """@resilient - Combines rate limiting + circuit breaking + Result[T, E] pattern.

    Catches all exceptions from the decorated function and converts them to Result.fail().
    Successful executions return Result.ok(data).

    Args:
        rps: Requests per second (enables rate limiting)
        burst: Burst size for rate limiting
        failures: Max failures before circuit opens
        window: Time window for circuit breaker (seconds)
        key: Custom key for rate limiting

    Examples:
        @resilient(rps=5.0)                    # Rate limiting only
        @resilient(failures=3)                 # Circuit breaker only
        @resilient(rps=10.0, failures=5)       # Both rate limit + circuit

    Returns:
        Decorator that converts function to return Result[T, E] instead of raising exceptions
    """

    def decorator(func: Callable[..., Union[T, Awaitable[T]]]) -> Callable[..., Union[Result, Awaitable[Result]]]:
        # Start with the original function
        wrapped = func

        # Apply circuit breaker if configured
        if failures is not None:
            wrapped = circuit(failures=failures, window=window or 300)(wrapped)

        # Apply rate limiting if configured
        if rps is not None:
            wrapped = rate_limit(rps=rps, burst=burst, key=key)(wrapped)

        # Determine if function is async
        is_async = hasattr(func, '__code__') and func.__code__.co_flags & 0x80

        if is_async:
            @functools.wraps(wrapped)
            async def async_result_wrapper(*args, **kwargs) -> Result:
                try:
                    result = await wrapped(*args, **kwargs)
                    return Result.ok(result)
                except Exception as e:
                    return Result.fail(str(e))
            return async_result_wrapper
        else:
            @functools.wraps(wrapped)
            def sync_result_wrapper(*args, **kwargs) -> Result:
                try:
                    result = wrapped(*args, **kwargs)
                    return Result.ok(result)
                except Exception as e:
                    return Result.fail(str(e))
            return sync_result_wrapper

    return decorator
