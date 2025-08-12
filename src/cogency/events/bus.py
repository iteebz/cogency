"""Core event emission infrastructure - stable and minimal."""

import asyncio
import functools
import time
from typing import Any, Optional

# Global bus instance
_bus: Optional["MessageBus"] = None


class MessageBus:
    """Core event bus - minimal and fast."""

    def __init__(self):
        self.handlers: list[Any] = []

    def subscribe(self, handler):
        """Add event handler."""
        self.handlers.append(handler)

    def emit(self, event_type: str, level: str = "info", **payload):
        """Emit event to all handlers with level."""
        event = {"type": event_type, "level": level, "data": payload, "timestamp": time.time()}
        for handler in self.handlers:
            handler.handle(event)


def init_bus(bus: "MessageBus") -> None:
    """Initialize global bus."""
    global _bus
    _bus = bus


def emit(event_type: str, level: str = "info", **data) -> None:
    """Emit to global bus if available with level."""
    if _bus:
        _bus.emit(event_type, level=level, **data)


def get_logs(
    *,
    type: str = None,
    errors_only: bool = False,
    last: int = None,
) -> list[dict]:
    """Get events from global event buffer with optional filtering."""
    if not _bus:
        return []

    # Find the EventBuffer in the bus
    for handler in _bus.handlers:
        if hasattr(handler, "logs"):
            return handler.logs(type=type, errors_only=errors_only, last=last)
    return []


# Canonical event decoration - one clear way to instrument operations
def emit_lifecycle(event_type: str, **meta):
    """Universal decorator for operation lifecycle events.

    Args:
        event_type: Event category (e.g. 'memory', 'security', 'config_load')
        **meta: Additional event metadata

    Usage:
        @emit_lifecycle('memory', operation='save')
        @emit_lifecycle('security', operation='assess')
        @emit_lifecycle('config_load', component='llm')
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
            emit(event_type, operation=operation, name=name, status="start", **clean_meta)
            try:
                result = await func(*args, **kwargs)
                # Extract additional result metadata if available
                result_meta = {}
                if hasattr(result, "safe"):
                    result_meta["safe"] = result.safe

                emit(
                    event_type,
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
            emit(event_type, operation=operation, name=name, status="start", **clean_meta)
            try:
                result = func(*args, **kwargs)
                result_meta = {}
                if hasattr(result, "safe"):
                    result_meta["safe"] = result.safe

                emit(
                    event_type,
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
                    operation=operation,
                    name=name,
                    status="error",
                    error=str(e),
                    **clean_meta,
                )
                raise

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


# Legacy compatibility - will be phased out
def lifecycle(event: str, **meta):
    """Deprecated: Use emit_lifecycle instead."""
    return emit_lifecycle(event, **meta)


def component(name: str):
    """Deprecated: Use emit_lifecycle('config_load', component=name) instead."""
    return emit_lifecycle("config_load", component=name)


def secure(func):
    """Deprecated: Use emit_lifecycle('security', operation='assess') instead."""
    return emit_lifecycle("security", operation="assess")(func)


def memory_op(operation: str):
    """Deprecated: Use emit_lifecycle('memory', operation=operation) instead."""
    return emit_lifecycle("memory", operation=operation)
