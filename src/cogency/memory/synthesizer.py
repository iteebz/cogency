"""LLM-driven user understanding synthesis."""

from datetime import datetime
from typing import Any, Dict, Optional

from cogency.state import Profile


class ImpressionSynthesizer:
    """LLM-driven user understanding synthesis with archival memory integration."""

    def __init__(self, provider, store=None, archival=None):
        self.provider = provider
        self.store = store
        self.archival = archival  # ArchivalMemory instance for topic storage
        self.synthesis_threshold = 3  # Synthesize every N interactions
        self.current_user_id = "default"  # Track current user for load/remember

    async def update_impression(self, user_id: str, interaction_data: Dict[str, Any]) -> Profile:
        """Update user impression from interaction with archival memory integration."""

        # Load existing profile
        profile = await self._load_profile(user_id)

        # Update interaction count only - insights extracted async post-response
        profile.interaction_count += 1
        profile.last_updated = datetime.now()

        # NOTE: Archival memory processing now handled by synthesis step
        # This reduces LLM calls and uses LLM-based topic extraction instead of heuristics

        # Save updated profile
        if self.store:
            await self._save_profile(profile)

        return profile

    async def _load_profile(self, user_id: str) -> Profile:
        """Load or create user profile using canonical StateStore methods."""
        if self.store:
            state_key = f"{user_id}:default"
            profile = await self.store.load_user_profile(state_key)
            if profile:
                return profile

        return Profile(user_id=user_id)

    async def _save_profile(self, profile: Profile) -> None:
        """Save profile to storage using canonical StateStore methods."""
        if not self.store:
            return

        state_key = f"{profile.user_id}:default"
        await self.store.save_user_profile(state_key, profile)

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
    # Legacy Archival Memory Methods (DEPRECATED - now handled by synthesis step)
    # 
    # These methods have been replaced by LLM-based archival processing in the synthesis step:
    # - _should_archive() -> Quality filtering now in synthesis prompt
    # - _extract_topic() -> LLM-based topic extraction in synthesis  
    # - _create_insight() -> Structured insight extraction in synthesis
    # - _process_archival_memory() -> Procedural pipeline in synthesize/core.py
    #
    # Keeping methods commented for reference during transition period

    async def load_archival(self, user_id: str = None) -> None:
        """Load archival memory for the current user."""
        if not self.archival:
            return
            
        target_user = user_id or self.current_user_id
        await self.archival.initialize(target_user)