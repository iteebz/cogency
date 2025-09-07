"""Consolidated error handling for LLM providers."""

from functools import wraps

from ...core.protocols import Event
from ..logger import logger


def handle_stream_errors(provider_name: str, import_package: str):
    """Decorator to handle common streaming errors across providers."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                async for chunk in func(*args, **kwargs):
                    yield chunk
            except ImportError:
                logger.error(f"Please install {import_package}: pip install {import_package}")
            except Exception as e:
                logger.error(f"{provider_name} Stream Error: {str(e)}")
            finally:
                # ALWAYS emit YIELD - prevents infinite hangs in replay mode
                yield Event.YIELD.delimiter

        return wrapper

    return decorator


def handle_generate_errors(provider_name: str, import_package: str):
    """Decorator to handle common generation errors across providers."""

    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ImportError:
                from ...core.result import Err

                return Err(f"Please install {import_package}: pip install {import_package}")
            except Exception as e:
                from ...core.result import Err

                return Err(f"{provider_name} Generate Error: {str(e)}")

        return wrapper

    return decorator
