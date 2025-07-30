"""Core notification infrastructure - v2 specification."""

import time
from dataclasses import dataclass, field
from inspect import iscoroutinefunction
from typing import Any, Callable, Dict, Optional


@dataclass
class Notification:
    """v2 Notification with structured data."""

    type: str
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)


async def emit(notification: Notification, callback: Optional[Callable] = None) -> None:
    """Emit notification with optional async callback."""
    if callback:
        if iscoroutinefunction(callback):
            await callback(notification)
        else:
            callback(notification)
