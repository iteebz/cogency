import asyncio
import logging
from collections.abc import AsyncGenerator, Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, cast

logger = logging.getLogger(__name__)

P = ParamSpec("P")
T = TypeVar("T")


def interruptible(
    func: Callable[..., AsyncGenerator[T, None]]
) -> Callable[..., AsyncGenerator[T, None]]:
    """Make async generator interruptible with clean EXECUTE emission."""

    @wraps(func)
    async def wrapper(self: Any, *args: Any, **kwargs: Any) -> AsyncGenerator[T, None]:
        provider_name = self.__class__.__name__
        try:
            async for chunk in func(self, *args, **kwargs):
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

    return cast(Callable[..., AsyncGenerator[T, None]], wrapper)
