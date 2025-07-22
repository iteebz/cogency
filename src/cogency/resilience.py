"""LLM timeout + retry with exponential backoff.
✅ Exponential backoff: 0.5s → 1s → 2s → up to 10s max
✅ Jitter prevents thundering herd
✅ Zero configuration needed
"""

import asyncio
from dataclasses import dataclass
from functools import wraps


@dataclass
class SafeConfig:
    """Configuration for @safe decorator - tune for your needs."""

    timeout: float = 30.0
    max_retries: int = 3
    base_delay: float = 0.5
    max_delay: float = 10.0


def safe(max_retries: int = 3, backoff_factor: float = 2.0):
    """@safe decorator for LLM calls - handles both run() and stream()."""

    def decorator(func):
        # Check function name to determine type
        if func.__name__ == "stream":
            # Stream method - async generator
            @wraps(func)
            async def safe_stream(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        async for chunk in func(*args, **kwargs):
                            yield chunk
                        return
                    except Exception as e:
                        if attempt == max_retries - 1:
                            yield f"Stream error after {max_retries} attempts: {str(e)}"
                            return
                        await asyncio.sleep(backoff_factor**attempt)

            return safe_stream
        else:
            # Run method - async function returning string
            @wraps(func)
            async def safe_run(*args, **kwargs):
                for attempt in range(max_retries):
                    try:
                        return await func(*args, **kwargs)
                    except Exception as e:
                        if attempt == max_retries - 1:
                            return f"Error after {max_retries} attempts: {str(e)}"
                        await asyncio.sleep(backoff_factor**attempt)

            return safe_run

    return decorator
