"""Conversation history management."""

from typing import Any

from ..lib.storage import load_conversations, save_conversations


class ConversationHistory:
    """User-scoped conversation and chat history management."""

    def format(self, user_id: str) -> str:
        """Format recent conversation history for context display."""
        try:
            messages = self.get(user_id)
            if not messages:
                return ""

            recent = messages[-5:] if len(messages) > 5 else messages
            lines = []
            for msg in recent:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:100]
                lines.append(f"{role}: {content}")

            return "Recent conversation:\n" + "\n".join(lines)
        except Exception:
            return ""

    def get(self, user_id: str) -> list[dict[str, Any]]:
        """Get conversation messages for user."""
        try:
            return load_conversations(user_id) or []
        except Exception:
            return []

    def add(self, user_id: str, role: str, content: str) -> bool:
        """Add message to conversation history."""
        try:
            messages = self.get(user_id)
            messages.append({"role": role, "content": content})
            save_conversations(user_id, messages)
            return True
        except Exception:
            return False

    def update(self, user_id: str, messages: list[dict[str, Any]]) -> bool:
        """Replace entire conversation history for user."""
        try:
            save_conversations(user_id, messages)
            return True
        except Exception:
            return False

    def clear(self, user_id: str) -> bool:
        """Clear conversation history for user."""
        return self.update(user_id, [])

    def get_recent(self, user_id: str, limit: int = 10) -> list[dict[str, Any]]:
        """Get recent messages with limit."""
        messages = self.get(user_id)
        return messages[-limit:] if len(messages) > limit else messages


# Singleton instance
conversation = ConversationHistory()
