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
            raise ValueError("user_id cannot be None")
        try:
            save_profile(user_id, profile_data)
            return True
        except Exception:
            return False

    def clear(self, user_id: str) -> bool:
        """Clear user profile data."""
        if user_id is None:
            raise ValueError("user_id cannot be None")
        return self.update(user_id, {})

    def set_preference(self, user_id: str, key: str, value: Any) -> bool:
        """Set specific preference for user."""
        profile = self.get(user_id) or {}
        profile[key] = value
        return self.update(user_id, profile)

    def get_preference(self, user_id: str, key: str, default: Any = None) -> Any:
        """Get specific preference for user."""
        profile = self.get(user_id)
        return profile.get(key, default) if profile else default


# Singleton instance
memory = UserMemory()
