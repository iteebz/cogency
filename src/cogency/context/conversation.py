"""Conversation history."""

from ..storage import history


def conversation(user_id: str) -> list[dict]:
    """Recent conversation history as structured messages."""
    try:
        messages = history(user_id)
        if not messages:
            return []

        # Return last 5 messages as proper message format
        recent = messages[-5:] if len(messages) > 5 else messages
        return [
            {"role": msg.get("role", "user"), "content": msg.get("content", "")}
            for msg in recent
            if msg.get("content")  # Skip empty messages
        ]
    except Exception:
        return []
