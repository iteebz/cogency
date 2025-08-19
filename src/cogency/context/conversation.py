"""Conversation history management."""

from typing import Any

from ..lib.storage import load_conversations, save_conversations


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
        return self.get(conversation_id, limit=limit)

    def get(self, conversation_id: str, limit: int = None) -> list[dict[str, Any]]:
        """Get conversation messages by conversation_id."""
        try:
            # Extract user_id from conversation_id pattern: user_id_timestamp
            if "_" in conversation_id:
                user_id = conversation_id.rsplit("_", 1)[0]
                messages = load_conversations(user_id) or []

                if limit is not None:
                    return messages[-limit:] if len(messages) > limit else messages
                return messages
            return []
        except Exception:
            return []

    def add(self, conversation_id: str, role: str, content: str) -> bool:
        """Add message to conversation history."""
        try:
            messages = self.get(conversation_id)
            messages.append({"role": role, "content": content})

            # Extract user_id for storage layer compatibility
            user_id = (
                conversation_id.rsplit("_", 1)[0] if "_" in conversation_id else conversation_id
            )
            save_conversations(user_id, messages)
            return True
        except Exception:
            return False

    def update(self, conversation_id: str, messages: list[dict[str, Any]]) -> bool:
        """Replace entire conversation history."""
        try:
            user_id = (
                conversation_id.rsplit("_", 1)[0] if "_" in conversation_id else conversation_id
            )
            save_conversations(user_id, messages)
            return True
        except Exception:
            return False

    def clear(self, conversation_id: str) -> bool:
        """Clear conversation history."""
        return self.update(conversation_id, [])


# Singleton instance
conversation = ConversationHistory()
