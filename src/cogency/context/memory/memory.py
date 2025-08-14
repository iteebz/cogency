"""Memory system - universal persistent context injection."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from cogency.events import emit


class Memory:
    """Universal memory system - canonical agent interface."""

    def __init__(self):
        """Initialize memory system with zero ceremony."""
        self._system = MemorySystem()

    async def activate(self, user_id: str, context: dict = None) -> str:
        """Activate memory context for runtime user and context."""
        return await self._system.activate(user_id, context)

    async def remember(self, user_id: str, content: str, human: bool = True) -> None:
        """Store interaction for learning."""
        await self._system.remember(user_id, content, human)

    # Legacy compatibility methods for existing Agent integration
    async def load(self, user_id: str) -> None:
        """Legacy load method - ensure profile exists."""
        await self._system._load_profile(user_id)

    def get_memory(self):
        """Legacy accessor method."""
        return self


@dataclass
class Profile:
    """User identity and preferences memory primitive.

    Direct context injection of user profile data for consistent
    agent behavior across sessions.
    """

    user_id: str
    preferences: dict[str, Any] = field(default_factory=dict)
    goals: list[str] = field(default_factory=list)
    expertise_areas: list[str] = field(default_factory=list)
    communication_style: str = ""
    projects: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def context(self) -> str:
        """Generate user context for agent injection."""
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
        """Legacy compatibility method for existing code."""
        result = self.context()
        return result[:max_tokens] if len(result) > max_tokens else result


class MemorySystem:
    """Intelligent runtime memory system - universal primitive management."""

    def __init__(self):
        # Internal primitive management - never exposed to users
        self._profiles = {}  # Profile primitives by user_id
        self._projects = {}  # Project memory primitives
        self._domains = {}  # Domain expertise primitives
        self._collaborative = {}  # Shared context primitives

    async def activate(self, user_id: str, context: dict = None) -> str:
        """Smart runtime activation of relevant memory primitives."""

        context = context or {}
        parts = []

        # Always activate Profile primitive for user context
        if user_id not in self._profiles:
            self._profiles[user_id] = await self._load_profile(user_id)

        profile_context = self._profiles[user_id].context()
        if profile_context:
            parts.append(f"USER CONTEXT:\n{profile_context}")

        # Future: Activate project memory if project_id in context
        # if context.get('project_id'):
        #     project_memory = await self._get_project_memory(context['project_id'])
        #     parts.append(f"PROJECT CONTEXT:\n{project_memory.context()}")

        # Future: Activate domain memory if domain in context
        # if context.get('domain'):
        #     domain_memory = await self._get_domain_memory(context['domain'])
        #     parts.append(f"DOMAIN EXPERTISE:\n{domain_memory.context()}")

        return "\n\n".join(parts) if parts else ""

    async def remember(self, user_id: str, content: str, human: bool = True) -> None:
        """Store interaction for user profile learning."""
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

    async def _load_profile(self, user_id: str) -> Profile:
        """Load or create user profile primitive."""
        from cogency.storage import SQLite

        store = SQLite()
        try:
            state_key = f"{user_id}:default"
            profile = await store.load_profile(state_key)
            if profile:
                return profile
        except Exception:
            # Fallback to new profile if storage fails
            pass

        return Profile(user_id=user_id)

    async def _update_profile(self, user_id: str, interaction_data: dict[str, Any]) -> None:
        """Update profile primitive with interaction data and extract learnings."""
        profile = self._profiles[user_id]
        profile.last_updated = datetime.now()

        # Extract learnings from interaction content
        if interaction_data.get("query") and interaction_data.get("human"):
            await self._extract_profile_insights(user_id, interaction_data["query"])

        # Save updated profile
        from cogency.storage import SQLite

        store = SQLite()
        try:
            state_key = f"{user_id}:default"
            await store.save_profile(state_key, profile)
        except Exception:
            # Ignore save errors - memory still works without persistence
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
                        result_data["content"] if isinstance(result_data, dict) and "content" in result_data else result_data
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
                    pass  # Ignore JSON parse errors

        except Exception:
            pass  # Ignore learning errors - don't break memory system
