"""Consolidated error handling for LLM providers."""

import asyncio
from functools import wraps

from ..logger import logger


def interruptible(func):
    """Make async generator interruptible with clean EXECUTE emission."""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        provider_name = self.__class__.__name__
        try:
            async for chunk in func(self, *args, **kwargs):
                yield chunk
        except KeyboardInterrupt:
            logger.info(f"{provider_name} interrupted by user (Ctrl+C)")
            raise  # Re-raise to propagate interrupt signal
        except asyncio.CancelledError:
            logger.debug(f"{provider_name} cancelled")
            raise  # Re-raise to propagate cancellation
        except Exception as e:
            logger.error(f"{provider_name} error: {str(e)}")
            # Emit END on error to cleanly terminate
            yield "§end"

    return wrapper
