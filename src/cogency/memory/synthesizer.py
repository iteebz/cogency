"""LLM-driven user understanding synthesis."""

from dataclasses import asdict
from datetime import datetime
from typing import Any, Dict

from cogency.state.agent import UserProfile


class ImpressionSynthesizer:
    """LLM-driven user understanding synthesis."""

    def __init__(self, llm, store=None):
        self.llm = llm
        self.store = store
        self.synthesis_threshold = 3  # Synthesize every N interactions
        self.current_user_id = "default"  # Track current user for load/remember

    async def update_impression(
        self, user_id: str, interaction_data: Dict[str, Any]
    ) -> UserProfile:
        """Update user impression from interaction."""

        # Load existing profile
        profile = await self._load_profile(user_id)

        # Update interaction count only - insights extracted async post-response
        profile.interaction_count += 1
        profile.last_updated = datetime.now()

        # Synthesis moved to async post-response processing

        # Save updated profile
        if self.store:
            await self._save_profile(profile)

        return profile

    async def _load_profile(self, user_id: str) -> UserProfile:
        """Load or create user profile."""
        if self.store:
            key = f"profile:{user_id}"
            try:
                result = await self.store.load(key)
            except AttributeError:
                # Fallback if store doesn't have load method
                return UserProfile(user_id=user_id)

            # Handle Result vs direct data response
            if hasattr(result, "success") and result.success:
                data = result.data
            elif isinstance(result, dict):
                data = result
            else:
                data = None

            if data and "state" in data:
                return UserProfile(**data["state"])
            elif data:
                return UserProfile(**data)
                # Direct profile data format

        return UserProfile(user_id=user_id)

    async def _save_profile(self, profile: UserProfile) -> None:
        """Save profile to storage."""
        if not self.store:
            return

        key = f"profile:{profile.user_id}"
        await self.store.save(key, asdict(profile))

    async def load(self, user_id: str = None) -> None:
        """Load memory state for the current user."""
        from cogency.events import emit

        if user_id:
            self.current_user_id = user_id

        emit("memory", operation="load", user_id=self.current_user_id, status="start")

        try:
            # Load profile to validate memory system
            profile = await self._load_profile(self.current_user_id)
            emit(
                "memory",
                operation="load",
                user_id=self.current_user_id,
                status="complete",
                interactions=profile.interaction_count,
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
        from cogency.events import emit

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
            profile = await self.update_impression(self.current_user_id, interaction_data)

            emit(
                "memory",
                operation="remember",
                user_id=self.current_user_id,
                status="complete",
                total_interactions=profile.interaction_count,
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
