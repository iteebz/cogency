"""Canonical notification system - Phase-based cognitive observability."""

import asyncio
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional


class Phase(Enum):
    """Canonical execution phases mapped to notification types."""

    PREPROCESS = "preprocess"
    REASON = "reason"
    ACTION = "action"
    RESPOND = "respond"
    TRACE = "trace"


@dataclass
class Notification:
    """Canonical notification structure."""

    phase: str
    message: str
    metadata: Dict[str, Any]


class Notifier:
    """Phase-based notification orchestrator - Clean callback decoupling."""

    def __init__(
        self, callback: Optional[Callable] = None, trace: bool = False, verbose: bool = True
    ):
        self.callback = callback
        self.trace_enabled = trace
        self.verbose = verbose
        self.notifications: list[Notification] = []

    def notify(self, phase: Phase, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Send canonical notification."""
        if phase == Phase.TRACE and not self.trace_enabled:
            return
        if phase != Phase.TRACE and not self.verbose:
            return

        notification = Notification(phase=phase.value, message=message, metadata=metadata or {})

        # Store notification
        self.notifications.append(notification)

        # Stream via callback if provided
        if self.callback:
            asyncio.create_task(self.callback(phase.value, message, metadata or {}))

    def preprocess(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Preprocessing phase notification."""
        self.notify(Phase.PREPROCESS, message, metadata)

    def reason(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Reasoning phase notification."""
        self.notify(Phase.REASON, message, metadata)

    def action(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Action/tool execution phase notification."""
        self.notify(Phase.ACTION, message, metadata)

    def respond(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Response generation phase notification."""
        self.notify(Phase.RESPOND, message, metadata)

    def trace(self, message: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Debug/trace notification."""
        self.notify(Phase.TRACE, message, metadata)


class NotificationFormatter:
    """Emoji formatting layer - Separated from data layer."""

    PHASE_EMOJIS = {
        Phase.PREPROCESS: "⚙️",
        Phase.REASON: "💭",
        Phase.ACTION: "⚡",
        Phase.RESPOND: "🤖",
        Phase.TRACE: "🔍",
    }

    @classmethod
    def format(cls, notification: Notification, include_emoji: bool = True) -> str:
        """Format notification with optional emoji."""
        if not include_emoji:
            return notification.message

        phase_enum = Phase(notification.phase)
        emoji = cls.PHASE_EMOJIS.get(phase_enum, "")
        return f"{emoji} {notification.message}" if emoji else notification.message

    @classmethod
    def format_thinking(cls, thinking: Optional[str], mode: str = "fast") -> str:
        """Format thinking content with mode-specific indicators."""
        if not thinking:
            return "Processing request..."

        emoji = "🧠" if mode == "deep" else "💭"
        return f"{emoji} {thinking}"


class NotificationStream:
    """Clean streaming interface for notifications."""

    def __init__(self, notifier: Notifier, formatter: NotificationFormatter = None):
        self.notifier = notifier
        self.formatter = formatter or NotificationFormatter()

    async def stream(self, include_emoji: bool = True):
        """Stream formatted notifications as they arrive."""
        for notification in self.notifier.notifications:
            yield self.formatter.format(notification, include_emoji)

    def get_by_phase(self, phase: Phase) -> list[Notification]:
        """Get all notifications for a specific phase."""
        return [n for n in self.notifier.notifications if n.phase == phase.value]
