import asyncio
import functools
import logging
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


def interruptable(func: F) -> F:
    """Decorator to handle asyncio.CancelledError for async functions.

    Provides clean cancellation handling across all async methods without
    cluttering business logic with try/except blocks.
    """

    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except asyncio.CancelledError:
            logger.info(f"Cancelled: {func.__name__}")
            raise  # Re-raise to propagate cancellation

    return wrapper
