"""Core event emission infrastructure - stable and minimal."""

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
        event = {"type": event_type, "level": level, "timestamp": time.time(), **payload}
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
