"""Core event emission infrastructure - stable and minimal."""

import functools
import time
from typing import Any, List, Optional

# Global bus instance
_bus: Optional["MessageBus"] = None


class MessageBus:
    """Core event bus - minimal and fast."""

    def __init__(self):
        self.handlers: List[Any] = []

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
    mode: str = None,
    type: str = None,
    step: str = None,
    summary: bool = None,
    errors_only: bool = False,
    last: int = None,
) -> List[dict]:
    """Get events from global logger handler with optional filtering."""
    if not _bus:
        return []

    # Handle backward compatibility - if mode is not provided, use summary parameter
    if mode is None:
        if summary is True:
            mode = "summary"
        elif errors_only:
            mode = "errors"
        else:
            mode = "debug"

    # Find the LoggerHandler in the bus
    for handler in _bus.handlers:
        if hasattr(handler, "logs"):
            return handler.logs(
                mode=mode, type=type, step=step, summary=summary, errors_only=errors_only, last=last
            )
    return []


# Beautiful decorators that fade into background
def lifecycle(event: str, **meta):
    """Decorator for lifecycle events (creation, teardown)."""

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            name = kwargs.get("name") or getattr(args[0], "name", "unknown")
            emit(event, name=name, **meta)
            try:
                result = await func(*args, **kwargs)
                emit(event, name=name, status="complete", **meta)
                return result
            except Exception as e:
                emit(event, name=name, status="error", error=str(e), **meta)
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            name = kwargs.get("name") or getattr(args[0], "name", "unknown")
            emit(event, name=name, **meta)
            try:
                result = func(*args, **kwargs)
                emit(event, name=name, status="complete", **meta)
                return result
            except Exception as e:
                emit(event, name=name, status="error", error=str(e), **meta)
                raise

        return async_wrapper if hasattr(func, "__await__") else sync_wrapper

    return decorator


def component(name: str):
    """Decorator for component setup/teardown."""

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            emit("config_load", component=name, status="loading")
            try:
                result = await func(*args, **kwargs)
                emit("config_load", component=name, status="complete")
                return result
            except Exception as e:
                emit("config_load", component=name, status="error", error=str(e))
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            emit("config_load", component=name, status="loading")
            try:
                result = func(*args, **kwargs)
                emit("config_load", component=name, status="complete")
                return result
            except Exception as e:
                emit("config_load", component=name, status="error", error=str(e))
                raise

        return async_wrapper if hasattr(func, "__await__") else sync_wrapper

    return decorator


def secure(func):
    """Decorator for security operations."""

    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        emit("security", operation="assess", status="checking")
        try:
            result = await func(*args, **kwargs)
            safe = getattr(result, "safe", True)
            emit("security", operation="assess", status="complete", safe=safe)
            return result
        except Exception as e:
            emit("security", operation="assess", status="error", error=str(e))
            raise

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        emit("security", operation="assess", status="checking")
        try:
            result = func(*args, **kwargs)
            safe = getattr(result, "safe", True)
            emit("security", operation="assess", status="complete", safe=safe)
            return result
        except Exception as e:
            emit("security", operation="assess", status="error", error=str(e))
            raise

    return async_wrapper if hasattr(func, "__await__") else sync_wrapper


def memory_op(operation: str):
    """Decorator for memory operations."""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            emit("memory", operation=operation, status="start")
            try:
                result = await func(*args, **kwargs)
                emit("memory", operation=operation, status="complete")
                return result
            except Exception as e:
                emit("memory", operation=operation, status="error", error=str(e))
                raise

        return wrapper

    return decorator
