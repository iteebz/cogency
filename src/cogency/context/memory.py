"""User profile."""

from ..storage import load_profile


def memory(user_id: str) -> str:
    """User profile context."""
    try:
        profile = load_profile(user_id)
        if not profile:
            return ""

        parts = []
        if profile.get("name"):
            parts.append(f"User: {profile['name']}")
        if profile.get("preferences"):
            prefs = ", ".join(profile["preferences"])
            parts.append(f"Interests: {prefs}")
        if profile.get("context"):
            parts.append(f"Context: {profile['context']}")

        return "User profile:\n" + "\n".join(parts) if parts else ""
    except Exception:
        return ""
