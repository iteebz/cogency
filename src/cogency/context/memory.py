"""User profile memory management."""

from typing import Any, Optional

from ..lib.storage import load_profile, save_profile


class UserMemory:
    """User-scoped profile and preference management."""

    def format(self, user_id: str) -> str:
        """Format user profile for context display."""
        try:
            profile = self.get(user_id)
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

    def get(self, user_id: str) -> Optional[dict[str, Any]]:
        """Get user profile data."""
        if user_id is None:
            raise ValueError("user_id cannot be None")
        try:
            return load_profile(user_id)
        except Exception:
            return None

    def update(self, user_id: str, profile_data: dict[str, Any]) -> bool:
        """Update user profile data."""
        if user_id is None:
            return False
        try:
            save_profile(user_id, profile_data)
            return True
        except Exception:
            return False

    def clear(self, user_id: str) -> bool:
        """Clear user profile data."""
        if user_id is None:
            return False
        return self.update(user_id, {})


# Singleton instance
memory = UserMemory()
