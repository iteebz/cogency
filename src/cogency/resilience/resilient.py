"""The magical @resilient decorator - combines all resilience patterns."""

from typing import Optional

from .circuit import circuit
from .rate_limit import rate_limit


def resilient(
    rps: Optional[float] = None,
    burst: Optional[int] = None,
    failures: Optional[int] = None,
    window: Optional[int] = None,
    key: Optional[str] = None,
):
    """@resilient - Combines rate limiting + circuit breaking in one magical decorator.

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
    """

    def decorator(func):
        # Start with the original function
        wrapped = func

        # Apply circuit breaker if configured
        if failures is not None:
            wrapped = circuit(failures=failures, window=window or 300)(wrapped)

        # Apply rate limiting if configured
        if rps is not None:
            wrapped = rate_limit(rps=rps, burst=burst, key=key)(wrapped)

        return wrapped

    return decorator
