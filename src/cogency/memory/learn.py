"""Profile learning from conversations - memory domain."""

import json

from cogency.events import emit
from cogency.providers import detect_llm


async def learn(state, memory) -> None:
    """Learn user profile patterns from conversation."""
    if not memory:
        return

    emit("memory", operation="learn_start", user_id=state.user_id)

    try:
        # Ensure profile exists in memory system
        await memory.activate(state.user_id)
        profile = memory._system._profiles.get(state.user_id)

        if not profile:
            emit("memory", operation="learn_error", error="No profile found")
            return

        # Build learning prompt with current profile context
        query = state.query
        response_content = ""

        # Get response from state execution context
        if hasattr(state, "execution") and hasattr(state.execution, "completed_calls"):
            # Try to get response from completed calls
            for call in state.execution.completed_calls:
                result = call.get("result", {})
                # Handle both dict and Result objects safely
                if hasattr(result, "get") and isinstance(result, dict) and result.get("result"):
                    response_content = result["result"]
                    break
                if hasattr(result, "is_ok") and hasattr(result, "unwrap"):
                    # Handle Result objects from resilient_result
                    if result.is_ok():
                        response_content = str(result.unwrap())
                        break
                elif isinstance(result, str):
                    # Handle direct string results
                    response_content = result
                    break

        # Fallback to checking workspace or other state locations
        if not response_content and hasattr(state, "workspace"):
            response_content = str(state.workspace.insights)

        current_preferences = profile.preferences
        current_goals = profile.goals
        current_expertise = profile.expertise_areas
        current_style = profile.communication_style

        prompt = f"""Analyze this interaction to update user profile:

INTERACTION:
Query: {query}
Response: {response_content}

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

        # Get LLM analysis using canonical provider
        llm = detect_llm()
        result = await llm.generate([{"role": "user", "content": prompt}])

        if not result.success:
            emit("memory", operation="learn_error", error="LLM call failed")
            return

        # Parse JSON response
        try:
            updates = json.loads(result.unwrap())
        except (json.JSONDecodeError, AttributeError):
            emit("memory", operation="learn_error", error="JSON parse failed")
            return

        # Apply updates to profile
        updated_fields = 0

        if "preferences" in updates and updates["preferences"]:
            profile.preferences.update(updates["preferences"])
            updated_fields += 1

        if "goals" in updates and updates["goals"]:
            for goal in updates["goals"]:
                if goal not in profile.goals:
                    profile.goals.append(goal)
            profile.goals = profile.goals[-10:]  # Keep recent goals
            updated_fields += 1

        if "expertise_areas" in updates and updates["expertise_areas"]:
            for area in updates["expertise_areas"]:
                if area not in profile.expertise_areas:
                    profile.expertise_areas.append(area)
            updated_fields += 1

        if "communication_style" in updates and updates["communication_style"]:
            profile.communication_style = updates["communication_style"]
            updated_fields += 1

        if "projects" in updates and updates["projects"]:
            profile.projects.update(updates["projects"])
            updated_fields += 1

        # Save updated profile through memory system
        if updated_fields > 0:
            await memory._system._update_profile(
                state.user_id, {"learning_update": True, "fields_updated": updated_fields}
            )

        emit("memory", operation="learn_complete", user_id=state.user_id, updates=updated_fields)

    except Exception as e:
        emit("memory", operation="learn_error", error=str(e))
        # Profile learning failures don't affect user experience
