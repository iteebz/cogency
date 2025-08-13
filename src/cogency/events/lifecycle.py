"""Lifecycle event decoration - canonical operation instrumentation."""

import asyncio
import functools

from .bus import emit


def lifecycle(event_type: str, **meta):
    """Universal decorator for operation lifecycle events.

    Args:
        event_type: Event category (e.g. 'memory', 'security', 'llm')
        **meta: Additional event metadata

    Usage:
        @lifecycle('memory', operation='save')
        @lifecycle('security', operation='assess')
        @lifecycle('llm', operation='generate')
    """

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Extract operation name from args or function name
            operation = meta.get("operation") or func.__name__
            name = kwargs.get("name") or (
                getattr(args[0], "name", "unknown") if args else "unknown"
            )

            # Create clean metadata without conflicts
            clean_meta = {k: v for k, v in meta.items() if k != "operation"}
            emit(
                event_type,
                level="debug",
                operation=operation,
                name=name,
                status="start",
                **clean_meta,
            )
            try:
                result = await func(*args, **kwargs)
                # Extract additional result metadata if available
                result_meta = {}
                if hasattr(result, "safe"):
                    result_meta["safe"] = result.safe

                emit(
                    event_type,
                    level="debug",
                    operation=operation,
                    name=name,
                    status="complete",
                    **clean_meta,
                    **result_meta,
                )
                return result
            except Exception as e:
                emit(
                    event_type,
                    level="debug",
                    operation=operation,
                    name=name,
                    status="error",
                    error=str(e),
                    **clean_meta,
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            operation = meta.get("operation") or func.__name__
            name = kwargs.get("name") or (
                getattr(args[0], "name", "unknown") if args else "unknown"
            )

            # Create clean metadata without conflicts
            clean_meta = {k: v for k, v in meta.items() if k != "operation"}
            emit(
                event_type,
                level="debug",
                operation=operation,
                name=name,
                status="start",
                **clean_meta,
            )
            try:
                result = func(*args, **kwargs)
                result_meta = {}
                if hasattr(result, "safe"):
                    result_meta["safe"] = result.safe

                emit(
                    event_type,
                    level="debug",
                    operation=operation,
                    name=name,
                    status="complete",
                    **clean_meta,
                    **result_meta,
                )
                return result
            except Exception as e:
                emit(
                    event_type,
                    level="debug",
                    operation=operation,
                    name=name,
                    status="error",
                    error=str(e),
                    **clean_meta,
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
