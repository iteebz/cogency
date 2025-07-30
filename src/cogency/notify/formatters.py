"""v2 Notification formatters - CLI, Emoji, JSON, Silent."""

import json
from typing import Any, Optional

from .core import Notification


class Formatter:
    """Base formatter class - silent by default."""

    def format(self, notification: Notification) -> Optional[str]:
        """Format notification. Returns None for silent mode (base class)."""
        return None  # Silent by default

    def _unknown(self, notification: Notification) -> str:
        """Handle unknown notification types."""
        return ""  # Return empty string for silent formatter

    def _unknown(self, notification: Notification) -> str:
        """Handle unknown notification types."""
        return ""  # Return empty string for silent formatter

    def _format_result(self, result: Any) -> str:
        """Format result data for display."""
        if result is None:
            return "completed"
        if isinstance(result, (dict, list)):
            return json.dumps(result, default=str)[:100] + ("..." if len(str(result)) > 100 else "")
        return str(result)[:100] + ("..." if len(str(result)) > 100 else "")


class CLIFormatter(Formatter):
    """Clean CLI formatter."""

    def format(self, notification: Notification) -> Optional[str]:
        """Format notification for CLI display."""
        return getattr(self, f"_{notification.type}", self._unknown)(notification)

    def _unknown(self, notification: Notification) -> str:
        """Handle unknown notification types for CLIFormatter."""
        return f"Unknown notification: {notification.type}"

    def _preprocess(self, notification: Notification) -> str:
        state = notification.data.get("state", "")
        return f"Preprocess {state}".strip()

    def _reason(self, notification: Notification) -> str:
        state = notification.data.get("state", "")
        return f"Reason {state}".strip()

    def _respond(self, notification: Notification) -> str:
        state = notification.data.get("state", "")
        return f"Respond {state}".strip()

    def _action(self, notification: Notification) -> str:
        state = notification.data.get("state", "")
        return f"Action {state}".strip()

    def _tool(self, notification: Notification) -> str:
        name = notification.data.get("name", "unknown_tool")
        if notification.data.get("ok"):
            result = self._format_result(notification.data.get("result"))
            return f"{name}: {result}"
        else:
            error = notification.data.get("error", "failed")
            return f"{name}: ERROR - {error}"

    def _memory(self, notification: Notification) -> str:
        content = notification.data.get("content", "")[:50]
        tags = notification.data.get("tags", [])
        return f"Memory saved: {content}{'...' if len(content) == 50 else ''} (tags: {', '.join(tags)})"

    def _trace(self, notification: Notification) -> str:
        message = notification.data.get("message", "Debug trace")
        return f"TRACE: {message}"


class EmojiFormatter(Formatter):
    """Emoji-rich formatter for enhanced UX."""

    def format(self, notification: Notification) -> Optional[str]:
        """Format notification with emojis."""
        return getattr(self, f"_{notification.type}", self._unknown)(notification)

    PHASE_EMOJIS = {"preprocess": "⚙️", "reason": "💭", "action": "⚡", "respond": "🤖", "trace": "🔍"}

    TOOL_EMOJIS = {
        "calculator": "🧮",
        "weather": "🌤️",
        "search": "🔍",
        "files": "📁",
        "memory": "🧠",
        "shell": "💻",
        "http": "🌐",
    }

    def _unknown(self, notification: Notification) -> str:
        """Handle unknown notification types."""
        return f"🔄 Unknown notification: {notification.type}"

    def _preprocess(self, notification: Notification) -> str:
        state = notification.data.get("state", "")
        return f"⚙️ Preprocess {state}".strip()

    def _reason(self, notification: Notification) -> str:
        state = notification.data.get("state", "")
        return f"💭 Reason {state}".strip()

    def _respond(self, notification: Notification) -> str:
        state = notification.data.get("state", "")
        return f"🤖 Respond {state}".strip()

    def _action(self, notification: Notification) -> str:
        state = notification.data.get("state", "")
        return f"⚡ Action {state}".strip()

    def _tool(self, notification: Notification) -> str:
        name = notification.data.get("name", "unknown_tool")
        emoji = self.TOOL_EMOJIS.get(name, "⚡")

        if notification.data.get("ok"):
            result = self._format_result(notification.data.get("result"))
            return f"{emoji} {name}: ✅ {result}"
        else:
            error = notification.data.get("error", "failed")
            return f"{emoji} {name}: ❌ {error}"

    def _memory(self, notification: Notification) -> str:
        content = notification.data.get("content", "")[:50]
        tags = notification.data.get("tags", [])
        return (
            f"🧠 Memory: ✅ {content}{'...' if len(content) == 50 else ''} (tags: {', '.join(tags)})"
        )

    def _trace(self, notification: Notification) -> str:
        message = notification.data.get("message", "Debug trace")
        return f"🔍 {message}"


class JSONFormatter(Formatter):
    """Structured JSON formatter."""

    def format(self, notification: Notification) -> str:
        """Always return JSON regardless of notification type."""
        return json.dumps(
            {"type": notification.type, "timestamp": notification.timestamp, **notification.data},
            default=str,
        )
