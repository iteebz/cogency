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

    def learn(self, user_id: str, query: str, response: str, context: str = None) -> None:
        """Learn from user interaction."""
        if not user_id or user_id == "default":
            return

        try:
            # Extract learnable patterns from interaction
            profile = self.get(user_id) or {}

            # Track interaction patterns
            interactions = profile.get("interactions", [])
            interactions.append(
                {
                    "query_type": self._classify_query(query),
                    "query_length": len(query),
                    "success": True,
                }
            )

            # Keep only recent interactions (last 50)
            interactions = interactions[-50:]

            # Extract preferences from successful queries
            preferences = profile.get("preferences", [])
            preferences = self._extract_preferences(query, response, preferences)

            # Update profile
            profile.update(
                {
                    "interactions": interactions,
                    "preferences": list(set(preferences)),  # Deduplicate
                    "last_active": int(__import__("time").time()),
                }
            )

            # Async update (non-blocking)
            self.update(user_id, profile)

        except Exception:
            # Memory updates never block - graceful degradation
            pass

    def _classify_query(self, query: str) -> str:
        """Classify query type for learning."""
        query_lower = query.lower()

        if any(word in query_lower for word in ["search", "find", "look up"]):
            return "search"
        if any(word in query_lower for word in ["create", "write", "generate"]):
            return "creation"
        if any(word in query_lower for word in ["explain", "what", "how", "why"]):
            return "explanation"
        if any(word in query_lower for word in ["analyze", "review", "check"]):
            return "analysis"
        return "general"

    def _extract_preferences(self, query: str, response: str, existing: list) -> list:
        """Extract user preferences from successful interactions."""
        preferences = existing.copy()

        # Extract topics/domains from query
        query_lower = query.lower()

        # Technical domains
        domains = ["python", "javascript", "react", "api", "database", "ml", "ai"]
        for domain in domains:
            if domain in query_lower and domain not in preferences:
                preferences.append(domain)

        # Limit to most recent 20 preferences
        return preferences[-20:]

    def clear(self, user_id: str) -> bool:
        """Clear user profile data."""
        if user_id is None:
            return False
        return self.update(user_id, {})


# Singleton instance
memory = UserMemory()
