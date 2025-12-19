import asyncio
import logging
from collections.abc import AsyncGenerator, Callable
from functools import wraps
from typing import ParamSpec, TypeVar

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")
SelfT = TypeVar("SelfT")


def interruptible(
    func: Callable[P, AsyncGenerator[T, None]],
) -> Callable[P, AsyncGenerator[T, None]]:
    """Make async generator interruptible. Preserves exact signature."""

    @wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> AsyncGenerator[T, None]:
        # Extract self from args for logging (first arg is always self for methods)
        provider_name = args[0].__class__.__name__ if args else "Unknown"
        try:
            async for chunk in func(*args, **kwargs):
                yield chunk
        except KeyboardInterrupt:
            logger.info(f"{provider_name} interrupted by user (Ctrl+C)")
            raise
        except asyncio.CancelledError:
            logger.debug(f"{provider_name} cancelled")
            raise
        except StopAsyncIteration:
            pass
        except Exception as e:
            if str(e):
                logger.error(f"{provider_name} error: {e!s}")
            raise

    return wrapper
