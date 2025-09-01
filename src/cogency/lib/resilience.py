"""Resilient operations - ripped from resilient-result, simplified."""

import time
from functools import wraps

from ..lib.logger import logger
from .storage import save_message


def retry(attempts: int = 3, base_delay: float = 0.1):
    """Simple retry decorator with exponential backoff - no Result ceremony."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(attempts):
                try:
                    result = func(*args, **kwargs)

                    # For save_message, treat False return as failure
                    if func == save_message and not result:
                        raise RuntimeError("Database save failed")

                    # Log success if we had retries
                    if attempt > 0:
                        logger.debug(f"{func.__name__} succeeded after {attempt + 1} attempts")

                    return result

                except Exception as e:
                    last_error = e

                    # If this is the last attempt, don't sleep or retry
                    if attempt < attempts - 1:
                        delay = base_delay * (2**attempt)
                        logger.debug(
                            f"Retrying {func.__name__} (attempt {attempt + 2}/{attempts}) after {type(e).__name__}: waiting {delay:.1f}s"
                        )
                        time.sleep(delay)

            # All attempts failed - log and return False for graceful degradation
            logger.debug(f"{func.__name__} failed after {attempts} attempts: {last_error}")
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


def safe_callback(callback, *args, **kwargs) -> None:
    """Execute callback with exception safety - don't crash streams."""
    if not callback:
        return

    try:
        callback(*args, **kwargs)
    except Exception as e:
        logger.error(f"Callback failed safely: {e}")
        # Continue execution - don't crash the stream
