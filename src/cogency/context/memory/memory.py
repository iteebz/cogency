"""Memory system - persistent context injection."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from cogency.events import emit


class Memory:
    """Memory system - agent persistence interface."""

    def __init__(self):
        self._profiles = {}  # Profiles by user_id
        self._projects = {}  # Project memory
        self._domains = {}  # Domain expertise
        self._collaborative = {}  # Shared context

    async def activate(self, user_id: str, context: dict = None) -> str:
        """Activate relevant memory for user."""
        context = context or {}
        parts = []

        # Load user profile
        if user_id not in self._profiles:
            self._profiles[user_id] = await self._load_profile(user_id)

        profile_context = self._profiles[user_id].context()
        if profile_context:
            parts.append(f"USER CONTEXT:\n{profile_context}")

        return "\n\n".join(parts) if parts else ""

    async def remember(self, user_id: str, content: str, human: bool = True) -> None:
        """Store interaction for learning."""
        emit(
            "memory",
            operation="remember",
            user_id=user_id,
            human=human,
            content_length=len(content),
            status="start",
        )

        try:
            # Ensure profile exists
            if user_id not in self._profiles:
                self._profiles[user_id] = await self._load_profile(user_id)

            # Update profile with interaction
            interaction_data = {
                "query" if human else "response": content,
                "success": True,
                "human": human,
            }
            await self._update_profile(user_id, interaction_data)

            emit(
                "memory",
                operation="remember",
                user_id=user_id,
                status="complete",
            )
        except Exception as e:
            emit(
                "memory",
                operation="remember",
                user_id=user_id,
                status="error",
                error=str(e),
            )
            raise

    async def load(self, user_id: str) -> None:
        """Ensure profile exists."""
        await self._load_profile(user_id)

    def get_memory(self):
        """Memory accessor method."""
        return self

    async def _load_profile(self, user_id: str) -> Profile:
        """Load or create user profile."""
        try:
            from cogency.storage.sqlite.profiles import load_profile

            state_key = f"{user_id}:default"
            profile = await load_profile(state_key)
            if profile:
                return profile
        except Exception:
            pass

        return Profile(user_id=user_id)

    async def _update_profile(self, user_id: str, interaction_data: dict[str, Any]) -> None:
        """Update profile with interaction data and extract learnings."""
        profile = self._profiles[user_id]
        profile.last_updated = datetime.now()

        # Extract learnings from interaction content
        if interaction_data.get("query") and interaction_data.get("human"):
            await self._extract_profile_insights(user_id, interaction_data["query"])

        # Save updated profile
        try:
            from cogency.storage.sqlite.profiles import save_profile

            state_key = f"{user_id}:default"
            await save_profile(state_key, profile)
        except Exception:
            pass

    async def _extract_profile_insights(self, user_id: str, content: str) -> None:
        """Extract profile insights from user content using LLM analysis."""
        try:
            import json
            from cogency.providers import detect_llm

            profile = self._profiles[user_id]

            # Build learning prompt
            prompt = f"""Extract user profile information from this message:

MESSAGE: {content}

CURRENT PROFILE:
- Communication style: {profile.communication_style}
- Preferences: {profile.preferences}
- Goals: {profile.goals}
- Expertise: {profile.expertise_areas}

Extract any clear profile information. Return JSON (omit empty fields):
{{
  "name_mentioned": "name if explicitly stated",
  "preferences": {{"key": "value"}},
  "goals": ["goal1"],
  "expertise_areas": ["skill1"],
  "communication_style": "description"
}}"""

            llm = detect_llm()
            result = await llm.generate([{"role": "user", "content": prompt}])

            if result.success:
                try:
                    result_data = result.value
                    response = (
                        result_data["content"]
                        if isinstance(result_data, dict) and "content" in result_data
                        else result_data
                        if hasattr(result, "value")
                        else result.unwrap()
                        if hasattr(result, "unwrap")
                        else str(result)
                    )

                    # Clean JSON from markdown code blocks
                    if "```json" in response:
                        response = response.split("```json")[1].split("```")[0].strip()
                    elif "```" in response:
                        response = response.split("```")[1].strip()

                    updates = json.loads(response)

                    # Apply updates
                    if "name_mentioned" in updates and updates["name_mentioned"]:
                        profile.preferences["name"] = updates["name_mentioned"]

                    if "preferences" in updates:
                        profile.preferences.update(updates["preferences"])

                    if "goals" in updates and updates["goals"]:
                        for goal in updates["goals"]:
                            if goal not in profile.goals:
                                profile.goals.append(goal)
                        profile.goals = profile.goals[-10:]

                    if "expertise_areas" in updates and updates["expertise_areas"]:
                        for area in updates["expertise_areas"]:
                            if area not in profile.expertise_areas:
                                profile.expertise_areas.append(area)

                    if "communication_style" in updates and updates["communication_style"]:
                        profile.communication_style = updates["communication_style"]

                except json.JSONDecodeError:
                    pass

        except Exception:
            pass


@dataclass
class Profile:
    """User identity and preferences."""

    user_id: str
    preferences: dict[str, Any] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    expertise_areas: list[str] = field(default_factory=list)
    communication_style: str = ""
    projects: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def context(self) -> str:
        """Generate user context for agent."""
        sections = []

        # Include user's name if mentioned
        if self.preferences.get("name"):
            sections.append(f"USER: {self.preferences['name']}")

        if self.communication_style:
            sections.append(f"COMMUNICATION: {self.communication_style}")

        if self.goals:
            goals_str = "; ".join(self.goals[-3:])
            sections.append(f"CURRENT GOALS: {goals_str}")

        if self.preferences:
            # Filter out name since it's handled separately
            prefs_items = [(k, v) for k, v in self.preferences.items() if k != "name"][-5:]
            if prefs_items:
                prefs_str = ", ".join(f"{k}: {v}" for k, v in prefs_items)
                sections.append(f"PREFERENCES: {prefs_str}")

        if self.projects:
            projects_items = list(self.projects.items())[-3:]
            projects_str = "; ".join(f"{k}: {v}" for k, v in projects_items)
            sections.append(f"ACTIVE PROJECTS: {projects_str}")

        if self.expertise_areas:
            expertise_str = ", ".join(self.expertise_areas[-5:])
            sections.append(f"EXPERTISE: {expertise_str}")

        return "\n".join(sections)

    def to_context(self, max_tokens: int = 800) -> str:
        """Context with token limit."""
        result = self.context()
        return result[:max_tokens] if len(result) > max_tokens else result

