"""Persistence utilities."""

from ..storage import load_conversations, load_profile, save_conversations, save_profile


async def persist(user_id: str, query: str, response: str):
    """Persist conversation."""
    try:
        messages = load_conversations(user_id)

        messages.extend(
            [
                {"role": "user", "content": query, "timestamp": __import__("time").time()},
                {"role": "assistant", "content": response, "timestamp": __import__("time").time()},
            ]
        )

        if len(messages) > 100:
            messages = messages[-100:]

        save_conversations(user_id, messages)
    except Exception:
        pass


def profile(user_id: str, name: str = None, preferences: list = None, context: str = None):
    """Set user profile."""
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
