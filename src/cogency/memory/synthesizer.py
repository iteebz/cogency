"""LLM-driven user understanding synthesis."""

from typing import Any, Dict

from cogency.persist.serialization import deserialize_profile, serialize_profile
from cogency.state.user_profile import UserProfile
from cogency.utils import parse_json

from .compression import compress_for_injection
from .insights import extract_insights


class ImpressionSynthesizer:
    """LLM-driven user understanding synthesis."""

    def __init__(self, llm, store=None):
        self.llm = llm
        self.store = store
        self.synthesis_threshold = 3  # Synthesize every N interactions

    async def update_impression(
        self, user_id: str, interaction_data: Dict[str, Any]
    ) -> UserProfile:
        """Update user impression from interaction."""

        # Load existing profile
        profile = await self._load_profile(user_id)

        # Extract insights from interaction
        insights = await extract_insights(self.llm, interaction_data)

        # Update profile with insights
        if insights:
            profile.update_from_interaction(insights)

        # Synthesize if threshold reached
        if profile.interaction_count % self.synthesis_threshold == 0:
            profile = await self._synthesize_profile(profile, interaction_data)

        # Save updated profile
        if self.store:
            await self._save_profile(profile)

        return profile

    async def _synthesize_profile(
        self, profile: UserProfile, recent_interaction: Dict[str, Any]
    ) -> UserProfile:
        """LLM-driven profile synthesis."""

        current_context = compress_for_injection(profile)

        prompt = f"""Synthesize evolved user profile:

CURRENT PROFILE:
{current_context}

RECENT INTERACTION:
Query: {recent_interaction.get('query', '')}
Success: {recent_interaction.get('success', True)}

Create refined profile that:
- Consolidates understanding over time
- Prioritizes recent patterns
- Eliminates contradictions
- Builds coherent user model

Return JSON with updated fields:
{{
    "preferences": {{}},
    "goals": [],
    "expertise_areas": [],
    "communication_style": "",
    "projects": {{}},
    "interests": [],
    "constraints": [],
    "success_patterns": [],
    "failure_patterns": []
}}"""

        result = await self.llm.run([{"role": "user", "content": prompt}])
        if result.success:
            parsed = parse_json(result.data)
            if parsed.success:
                self._apply_synthesis_to_profile(profile, parsed.data)
                profile.synthesis_version += 1

        return profile

    def _apply_synthesis_to_profile(
        self, profile: UserProfile, synthesis_data: Dict[str, Any]
    ) -> None:
        """Apply LLM synthesis to profile."""
        for key, value in synthesis_data.items():
            if hasattr(profile, key) and value:
                setattr(profile, key, value)

    async def _load_profile(self, user_id: str) -> UserProfile:
        """Load or create user profile."""
        if self.store:
            key = f"profile:{user_id}"
            result = await self.store.load(key)

            # Handle Result vs direct data response
            if hasattr(result, "success") and result.success:
                data = result.data
            elif isinstance(result, dict):
                data = result
            else:
                data = None

            if data and "state" in data:
                profile_data = data["state"]
                return deserialize_profile(profile_data)
            elif data:
                # Direct profile data format
                return deserialize_profile(data)

        return UserProfile(user_id=user_id)

    async def _save_profile(self, profile: UserProfile) -> None:
        """Save profile to storage."""
        if not self.store:
            return

        key = f"profile:{profile.user_id}"
        profile_dict = serialize_profile(profile)
        await self.store.save(key, profile_dict)
