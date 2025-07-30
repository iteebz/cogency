"""v2 Notifier - Clean async notification orchestrator."""

from typing import Any, Callable, Dict, Optional

from .core import Notification
from .formatters import Formatter


class Notifier:
    """v2 async notification orchestrator."""

    def __init__(self, formatter: Formatter, on_notify: Optional[Callable] = None):
        self.formatter = formatter
        self.on_notify = on_notify
        self.notifications = []

    async def __call__(self, event_type: str, **data) -> None:
        """Pure event dispatcher - notifier(type, **payload)."""
        notification = Notification(type=event_type, data=data)
        self.notifications.append(notification)

        # Format and emit
        formatted = self.formatter.format(notification)
        if formatted and self.on_notify:  # None for silent mode
            from .core import emit as core_emit

            await core_emit(notification, self.on_notify)

    async def emit(self, notification_type: str, data: Dict[str, Any]) -> None:
        """Legacy emit method - kept for backward compatibility."""
        await self(notification_type, **data)

    # Old v2 methods removed - use ultimate callable form: await notifier("event_type", **data)
