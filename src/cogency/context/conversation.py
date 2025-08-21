"""Conversation history management."""

from typing import Any

from ..lib.storage import load_conversations, save_conversation_message


class ConversationHistory:
    """User-scoped conversation and chat history management."""

    def format(self, conversation_id: str) -> str:
        """Format recent conversation history for context display."""
        try:
            messages = self.get(conversation_id)
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

    def messages(self, conversation_id: str, limit: int = 20) -> list[dict[str, Any]]:
        """Get conversation history as structured messages for LLM context."""
        messages = self.get(conversation_id, limit=limit)

        # Filter out corrupted messages with null content
        valid_messages = []
        for msg in messages:
            if isinstance(msg.get("content"), str) and msg.get("role"):
                valid_messages.append(msg)

        return valid_messages

    def get(self, conversation_id: str, limit: int = None) -> list[dict[str, Any]]:
        """Get conversation messages by conversation_id."""
        try:
            messages = load_conversations(conversation_id)
            if limit is not None:
                return messages[-limit:] if len(messages) > limit else messages
            return messages
        except Exception:
            return []

    def add(self, conversation_id: str, role: str, content: str) -> bool:
        """Add message to conversation history - O(1) SQLite operation."""
        return save_conversation_message(conversation_id, role, content)


# Singleton instance
conversation = ConversationHistory()
