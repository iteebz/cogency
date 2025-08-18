"""Conversation history."""

from ..lib.storage import load_conversations


def conversation(user_id: str) -> str:
    """Recent conversation history."""
    try:
        messages = load_conversations(user_id)
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
