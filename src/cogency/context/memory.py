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

    async def learn(
        self, user_id: str, query: str, response: str, context: str = None, llm=None
    ) -> None:
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
            preferences = await self._extract_preferences(query, response, preferences, llm)

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

    async def _extract_preferences(
        self, query: str, response: str, existing: list, llm=None
    ) -> list:
        """Extract user preferences with LLM enhancement and keyword fallback."""
        preferences = existing.copy()

        if llm:
            # LLM-powered pattern extraction
            try:
                llm_preferences = await self._llm_extract_patterns(query, response, existing, llm)
                if llm_preferences:
                    preferences.extend(llm_preferences)
            except Exception:
                # Graceful degradation to keyword extraction
                pass

        # Keyword extraction fallback (always runs)
        keyword_preferences = self._keyword_extract_patterns(query)
        preferences.extend(keyword_preferences)

        # Deduplicate and limit to most recent 20 preferences
        seen = set()
        unique_preferences = []
        for pref in reversed(preferences):  # Keep most recent duplicates
            if pref not in seen:
                seen.add(pref)
                unique_preferences.append(pref)

        return list(reversed(unique_preferences))[-20:]

    async def _llm_extract_patterns(self, query: str, response: str, existing: list, llm) -> list:
        """Use LLM to extract user interests and expertise patterns."""
        try:
            extraction_prompt = f"""Extract user interests and expertise from this interaction.

Query: {query}
Response: {response[:200]}...

Current interests: {existing}

Extract 1-3 specific topics/domains the user is interested in or working with.
Return only a comma-separated list of topics, no explanation.
Examples: python, machine learning, web development, data analysis

Topics:"""

            # Simple LLM call for pattern extraction
            result = await llm.generate([{"role": "user", "content": extraction_prompt}])
            if result and hasattr(result, "success") and result.success:
                llm_response = result.unwrap().strip()
                # Parse comma-separated topics
                topics = [topic.strip().lower() for topic in llm_response.split(",")]
                return [topic for topic in topics if topic and len(topic) > 2]

        except Exception:
            pass

        return []

    def _keyword_extract_patterns(self, query: str) -> list:
        """Keyword-based pattern extraction fallback."""
        preferences = []
        query_lower = query.lower()

        # Technical domains
        domains = [
            "python",
            "javascript",
            "react",
            "api",
            "database",
            "ml",
            "ai",
            "typescript",
            "node",
            "docker",
            "kubernetes",
            "aws",
            "azure",
            "machine learning",
            "data science",
            "web development",
            "backend",
            "frontend",
            "full stack",
            "devops",
            "security",
            "testing",
        ]

        for domain in domains:
            if domain in query_lower and domain not in preferences:
                preferences.append(domain)

        return preferences

    def clear(self, user_id: str) -> bool:
        """Clear user profile data."""
        if user_id is None:
            return False
        return self.update(user_id, {})


# Singleton instance
memory = UserMemory()
