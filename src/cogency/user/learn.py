"""User profile learning from conversations."""

import json

from cogency.events import emit


async def learn(state, memory) -> None:
    """Learn user profile patterns from conversation."""
    if not memory:
        return

    emit("user", state="learn_start", user_id=state.user_id)

    try:
        # Build learning prompt with current profile context
        query = state.query
        response = state.execution.response or ""
        profile = state.profile

        current_preferences = profile.preferences if profile else {}
        current_goals = profile.goals if profile else []
        current_expertise = profile.expertise_areas if profile else []
        current_style = profile.communication_style if profile else ""

        prompt = f"""Analyze this interaction to update user profile:

INTERACTION:
Query: {query}
Response: {response}

CURRENT PROFILE:
Preferences: {current_preferences}
Goals: {current_goals}
Expertise: {current_expertise}
Communication Style: {current_style}

Extract profile updates based on clear evidence from this interaction:
- User preferences and working styles
- Professional goals and interests
- Technical expertise and knowledge areas
- Communication preferences

Return JSON (omit empty fields):
{{
  "preferences": {{"key": "value"}},
  "goals": ["goal1", "goal2"],
  "expertise_areas": ["skill1", "skill2"],
  "communication_style": "description"
}}"""

        # Get LLM analysis
        result = await memory.provider.generate([{"role": "user", "content": prompt}])
        if not result.success:
            emit("user", state="learn_error", error="LLM call failed")
            return

        # Parse JSON response
        try:
            updates = json.loads(result.data)
        except (json.JSONDecodeError, AttributeError):
            emit("user", state="learn_error", error="JSON parse failed")
            return

        # Apply updates to profile
        if "preferences" in updates:
            profile.preferences.update(updates["preferences"])

        if "goals" in updates:
            for goal in updates["goals"]:
                if goal not in profile.goals:
                    profile.goals.append(goal)
            profile.goals = profile.goals[-10:]  # Keep recent goals

        if "expertise_areas" in updates:
            for area in updates["expertise_areas"]:
                if area not in profile.expertise_areas:
                    profile.expertise_areas.append(area)

        if "communication_style" in updates:
            profile.communication_style = updates["communication_style"]

        if "projects" in updates:
            profile.projects.update(updates["projects"])

        # Save updated profile
        if hasattr(memory, "_save_profile"):
            await memory._save_profile(profile)

        emit("user", state="learn_complete", user_id=state.user_id, updates=len(updates))

    except Exception as e:
        emit("user", state="learn_error", error=str(e))
        # Profile learning failures don't affect user experience
