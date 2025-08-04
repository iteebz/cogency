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

    def emit(self, event_type: str, **payload):
        """Emit event to all handlers."""
        event = {"type": event_type, "data": payload, "timestamp": time.time()}
        for handler in self.handlers:
            handler.handle(event)


def init_bus(bus: "MessageBus") -> None:
    """Initialize global bus."""
    global _bus
    _bus = bus


def emit(event_type: str, **data) -> None:
    """Emit to global bus if available."""
    if _bus:
        _bus.emit(event_type, **data)


def get_logs() -> List[dict]:
    """Get all events from global logger handler."""
    if not _bus:
        return []

    # Find the LoggerHandler in the bus
    for handler in _bus.handlers:
        if hasattr(handler, "logs"):
            return handler.logs()
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
