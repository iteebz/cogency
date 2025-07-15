"""Clean retry decorator - single responsibility."""
from functools import wraps
import asyncio


def retry(max_attempts=3, delay=0.1):
    """Clean retry decorator - handles retries only."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (2 ** attempt))  # Exponential backoff
                        continue
                    else:
                        raise last_error
            raise last_error
        return wrapper
    return decorator