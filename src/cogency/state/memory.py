"""Situated Memory - User understanding that evolves over time."""

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List

from cogency.utils import parse_json


@dataclass
class UserProfile:
    """Persistent user understanding - builds over time."""

    user_id: str

    # Core Understanding
    preferences: Dict[str, Any] = field(default_factory=dict)
    goals: List[str] = field(default_factory=list)
    expertise_areas: List[str] = field(default_factory=list)
    communication_style: str = ""

    # Contextual Knowledge
    projects: Dict[str, str] = field(default_factory=dict)
    interests: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)

    # Interaction Patterns
    success_patterns: List[str] = field(default_factory=list)
    failure_patterns: List[str] = field(default_factory=list)

    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    interaction_count: int = 0
    synthesis_version: int = 1

    def compress_for_injection(self, max_tokens: int = 800) -> str:
        """Generate situated context for agent initialization."""
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

        if self.constraints:
            constraints_str = "; ".join(self.constraints[-3:])
            sections.append(f"CONSTRAINTS: {constraints_str}")

        result = "\n".join(sections)
        return result[:max_tokens] if len(result) > max_tokens else result

    def update_from_interaction(self, interaction_insights: Dict[str, Any]) -> None:
        """Update profile from interaction insights."""
        self.interaction_count += 1
        self.last_updated = datetime.now()

        # Update preferences
        if "preferences" in interaction_insights:
            self.preferences.update(interaction_insights["preferences"])

        # Add new goals (bounded)
        if "goals" in interaction_insights:
            for goal in interaction_insights["goals"]:
                if goal not in self.goals:
                    self.goals.append(goal)
            if len(self.goals) > 10:
                self.goals = self.goals[-10:]

        # Update expertise areas
        if "expertise" in interaction_insights:
            for area in interaction_insights["expertise"]:
                if area not in self.expertise_areas:
                    self.expertise_areas.append(area)
            if len(self.expertise_areas) > 15:
                self.expertise_areas = self.expertise_areas[-15:]

        # Update communication style
        if "communication_style" in interaction_insights:
            self.communication_style = interaction_insights["communication_style"]

        # Update project context
        if "project_context" in interaction_insights:
            self.projects.update(interaction_insights["project_context"])
            if len(self.projects) > 10:
                # Keep most recent projects
                items = list(self.projects.items())[-10:]
                self.projects = dict(items)

        # Track success/failure patterns
        if "success_pattern" in interaction_insights:
            pattern = interaction_insights["success_pattern"]
            if pattern and pattern not in self.success_patterns:
                self.success_patterns.append(pattern)
                if len(self.success_patterns) > 5:
                    self.success_patterns = self.success_patterns[-5:]

        if "failure_pattern" in interaction_insights:
            pattern = interaction_insights["failure_pattern"]
            if pattern and pattern not in self.failure_patterns:
                self.failure_patterns.append(pattern)
                if len(self.failure_patterns) > 5:
                    self.failure_patterns = self.failure_patterns[-5:]


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
        insights = await self._extract_insights(interaction_data)

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

    async def _extract_insights(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract insights from single interaction."""

        query = interaction_data.get("query", "")
        response = interaction_data.get("response", "")
        success = interaction_data.get("success", True)

        prompt = f"""Extract user insights from this interaction:

User Query: {query}
Agent Response: {response}
Success: {success}

Extract insights about:
- User goals and preferences
- Technical expertise level  
- Communication preferences
- Project context
- Success/failure patterns

Return JSON:
{{
    "preferences": {{"key": "value"}},
    "goals": ["goal1", "goal2"],
    "expertise": ["area1", "area2"],
    "communication_style": "concise|detailed|technical",
    "project_context": {{"project_name": "description"}},
    "success_pattern": "what worked",
    "failure_pattern": "what didn't work"
}}"""

        result = await self.llm.run([{"role": "user", "content": prompt}])
        if result.success:
            parsed = parse_json(result.data)
            return parsed.data if parsed.success else {}
        return {}

    async def _synthesize_profile(
        self, profile: UserProfile, recent_interaction: Dict[str, Any]
    ) -> UserProfile:
        """LLM-driven profile synthesis."""

        current_context = profile.compress_for_injection()

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
                # Handle datetime deserialization
                if "created_at" in profile_data:
                    profile_data["created_at"] = datetime.fromisoformat(profile_data["created_at"])
                if "last_updated" in profile_data:
                    profile_data["last_updated"] = datetime.fromisoformat(
                        profile_data["last_updated"]
                    )
                return UserProfile(**profile_data)
            elif data:
                # Direct profile data format
                profile_data = data.copy()
                # Handle datetime deserialization
                if "created_at" in profile_data:
                    profile_data["created_at"] = datetime.fromisoformat(profile_data["created_at"])
                if "last_updated" in profile_data:
                    profile_data["last_updated"] = datetime.fromisoformat(
                        profile_data["last_updated"]
                    )
                return UserProfile(**profile_data)

        return UserProfile(user_id=user_id)

    async def _save_profile(self, profile: UserProfile) -> None:
        """Save profile to storage."""
        if not self.store:
            return

        key = f"profile:{profile.user_id}"

        # Convert to dict for storage
        profile_dict = asdict(profile)
        profile_dict["created_at"] = profile.created_at.isoformat()
        profile_dict["last_updated"] = profile.last_updated.isoformat()

        await self.store.save(key, profile_dict)
