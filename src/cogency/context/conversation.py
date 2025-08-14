"""Conversation: Recent conversation history for continuity."""

from ..storage import load_conversations


def conversation(user_id: str) -> str:
    """Recent conversation history for continuity."""
    try:
        messages = load_conversations(user_id)
        if not messages:
            return ""

        # Format last 5 messages for context
        recent = messages[-5:] if len(messages) > 5 else messages
        formatted = []
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")[:100]  # Truncate for brevity
            formatted.append(f"{role}: {content}")

        return "Recent conversation:\n" + "\n".join(formatted)
    except Exception:
        return ""  # Graceful degradation
