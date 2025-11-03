import asyncio
import logging
from functools import wraps

logger = logging.getLogger(__name__)


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
            raise
        except asyncio.CancelledError:
            logger.debug(f"{provider_name} cancelled")
            raise
        except StopAsyncIteration:
            pass
        except Exception as e:
            if str(e):
                logger.error(f"{provider_name} error: {str(e)}")
            raise  # Re-raise the exception

    return wrapper
