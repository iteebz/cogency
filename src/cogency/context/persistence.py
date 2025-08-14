"""Persistence: Conversation and profile persistence utilities."""

from ..storage import load_conversations, load_profile, save_conversations, save_profile


async def persist_conversation_async(user_id: str, query: str, response: str):
    """Optional conversation persistence - fire and forget."""
    try:
        messages = load_conversations(user_id)

        # Append user query and assistant response
        messages.extend(
            [
                {"role": "user", "content": query, "timestamp": __import__("time").time()},
                {"role": "assistant", "content": response, "timestamp": __import__("time").time()},
            ]
        )

        # Keep only last 100 messages to prevent unbounded growth
        if len(messages) > 100:
            messages = messages[-100:]

        save_conversations(user_id, messages)
    except Exception:
        pass  # Fire and forget - don't fail if persistence breaks


def set_user_profile(user_id: str, name: str = None, preferences: list = None, context: str = None):
    """Set user profile for personalization."""
    try:
        profile = load_profile(user_id)

        # Update profile fields
        if name is not None:
            profile["name"] = name
        if preferences is not None:
            profile["preferences"] = preferences
        if context is not None:
            profile["context"] = context

        return save_profile(user_id, profile)
    except Exception:
        return False
