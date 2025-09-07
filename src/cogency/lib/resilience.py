"""Resilient operations - ripped from resilient-result, simplified."""

import asyncio
import time
from functools import wraps

from ..core.result import Err
from ..lib.logger import logger
from .storage import save_message


def retry(attempts: int = 3, base_delay: float = 0.1):
    """Simple retry decorator with exponential backoff - no Result ceremony."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(attempts):
                try:
                    result = func(*args, **kwargs)

                    # For save_message, treat False return as failure
                    if func == save_message and not result:
                        raise RuntimeError("Database save failed")

                    return result

                except Exception:
                    # If this is the last attempt, don't sleep or retry
                    if attempt < attempts - 1:
                        delay = base_delay * (2**attempt)
                        time.sleep(delay)

            # All attempts failed - return False for graceful degradation
            return False

        return wrapper

    return decorator


# Resilient save - single point of DB persistence
@retry(attempts=3, base_delay=0.1)
def resilient_save(
    conversation_id: str, user_id: str, msg_type: str, content: str, timestamp: float = None
) -> bool:
    """Save with retry logic - wraps storage.save_message."""
    return save_message(
        conversation_id, user_id, msg_type, content, base_dir=None, timestamp=timestamp
    )


def timeout(seconds: float = 30):
    """Simple timeout decorator for async functions."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(func(*args, **kwargs), timeout=seconds)
            except asyncio.TimeoutError:
                return Err(f"Operation timed out after {seconds}s")

        return wrapper

    return decorator


def safe_callback(callback, *args, **kwargs) -> None:
    """Execute callback with exception safety - don't crash streams."""
    if not callback:
        return

    try:
        callback(*args, **kwargs)
    except Exception as e:
        logger.error(f"Callback failed safely: {e}")
        # Continue execution - don't crash the stream
