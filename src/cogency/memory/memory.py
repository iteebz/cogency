"""Memory system - universal persistent context injection."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from cogency.events import emit


class Memory(ABC):
    """Universal persistent context injection interface."""

    @abstractmethod
    def load(self, context_id: str) -> None:
        """Load persistent context from storage."""
        pass

    @abstractmethod
    def context(self) -> str:
        """Generate context string for agent injection."""
        pass

    @abstractmethod
    def remember(self, content: str, metadata: dict = None) -> None:
        """Update persistent context with new information."""
        pass


@dataclass
class Profile(Memory):
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

        if self.communication_style:
            sections.append(f"COMMUNICATION: {self.communication_style}")

        if self.goals:
            goals_str = "; ".join(self.goals[-3:])
            sections.append(f"CURRENT GOALS: {goals_str}")

        if self.preferences:
            prefs_items = list(self.preferences.items())[-5:]
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

    def load(self, context_id: str) -> None:
        """Load profile context - basic implementation."""
        # Profile instances are loaded by MemoryManager
        pass

    def remember(self, content: str, metadata: dict = None) -> None:
        """Update profile with new information - basic implementation."""
        # Profile updates handled by MemoryManager
        self.last_updated = datetime.now()


class Memories:
    """Agent memory system - profile management and context injection."""

    def __init__(self, provider, store=None):
        self.provider = provider
        self.store = store
        self.current_user_id = "default"  # Track current user for load/remember

    async def update(self, user_id: str, interaction_data: dict[str, Any]) -> Profile:
        """Update user profile from interaction with knowledge system integration."""

        # Load existing profile
        profile = await self._load_profile(user_id)

        # Update interaction count and timestamp - profile learning handled async post-response
        profile.last_updated = datetime.now()

        # NOTE: Topic processing handled by separate Knowledge system (orthogonal design)

        # Save updated profile
        if self.store:
            await self._save_profile(profile)

        return profile

    async def _load_profile(self, user_id: str) -> Profile:
        """Load or create user profile using canonical StateStore methods."""
        if self.store:
            state_key = f"{user_id}:default"
            profile = await self.store.load_profile(state_key)
            if profile:
                return profile

        return Profile(user_id=user_id)

    async def _save_profile(self, profile: Profile) -> None:
        """Save profile to storage using canonical StateStore methods."""
        if not self.store:
            return

        state_key = f"{profile.user_id}:default"
        await self.store.save_profile(state_key, profile)

    async def load(self, user_id: str = None) -> None:
        """Load memory state for the current user."""
        if user_id:
            self.current_user_id = user_id

        emit("memory", operation="load", user_id=self.current_user_id, status="start")

        try:
            # Load profile to validate memory system
            await self._load_profile(self.current_user_id)
            emit(
                "memory",
                operation="load",
                user_id=self.current_user_id,
                status="complete",
            )
        except Exception as e:
            emit(
                "memory",
                operation="load",
                user_id=self.current_user_id,
                status="error",
                error=str(e),
            )
            raise

    async def remember(self, content: str, human: bool = True) -> None:
        """Store interaction for future processing - no LLM calls."""
        emit(
            "memory",
            operation="remember",
            user_id=self.current_user_id,
            human=human,
            content_length=len(content),
            status="start",
        )

        try:
            interaction_data = {
                "query" if human else "response": content,
                "success": True,
                "human": human,
            }
            # Pure data storage - no LLM processing
            await self.update(self.current_user_id, interaction_data)

            emit(
                "memory",
                operation="remember",
                user_id=self.current_user_id,
                status="complete",
            )
        except Exception as e:
            emit(
                "memory",
                operation="remember",
                user_id=self.current_user_id,
                status="error",
                error=str(e),
            )
            raise
