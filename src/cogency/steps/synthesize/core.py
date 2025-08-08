"""Core synthesis logic - orchestrates user understanding consolidation."""

import json
from datetime import datetime
from typing import Any, Dict, Optional

from cogency.events import emit
from cogency.state import State

from .prompt import build_synthesis_prompt


async def synthesize(state: State, memory) -> None:
    """Synthesis step - consolidates memory based on triggers."""
    if not memory:
        return

    emit("synthesize", state="start", user_id=state.user_id)

    # Check synthesis triggers
    user_profile = state.profile or await memory._load_profile(state.user_id)

    if not _should_synthesize(user_profile, state):
        emit("synthesize", state="skipped", reason="no_trigger")
        return

    # Check idempotence - prevent duplicate synthesis
    if _synthesis_in_progress(user_profile):
        emit("synthesize", state="skipped", reason="already_running")
        return

    try:
        # Mark synthesis in progress
        _mark_synthesis_start(user_profile)

        # Async synthesis to prevent blocking
        emit("synthesize", state="executing", synthesis_type="async")
        await _execute_synthesis(memory, state.user_id, user_profile, state)

        emit("synthesize", state="complete", user_id=state.user_id)

    except Exception as e:
        emit("synthesize", state="error", error=str(e))
        # Synthesis failures don't affect user experience
    finally:
        _mark_synthesis_complete(user_profile)


def _should_synthesize(user_profile, state: State) -> bool:
    """Check if synthesis should trigger based on OR conditions."""
    if not user_profile:
        return False

    # Condition 1: Threshold reached
    threshold_reached = _check_threshold(user_profile)

    # Condition 2: Session ending
    session_ending = _check_session_end(user_profile, state)

    # Condition 3: High value interaction (optional)
    high_value = _check_high_value_interaction(state)

    return threshold_reached or session_ending or high_value


def _check_threshold(user_profile) -> bool:
    """Check if interaction threshold reached since last synthesis."""
    threshold = getattr(user_profile, "synthesis_threshold", 5)
    interactions_since = user_profile.interaction_count - getattr(
        user_profile, "last_synthesis_count", 0
    )
    return interactions_since >= threshold


def _check_session_end(user_profile, state: State) -> bool:
    """Detect session ending based on time gap."""
    if not hasattr(user_profile, "last_interaction_time"):
        return False

    last_time = user_profile.last_interaction_time
    if not last_time:
        return False

    # Convert string to datetime if needed
    if isinstance(last_time, str):
        try:
            last_time = datetime.fromisoformat(last_time)
        except ValueError:
            return False

    session_timeout = getattr(user_profile, "session_timeout", 1800)  # 30 minutes
    time_gap = datetime.now() - last_time
    return time_gap.total_seconds() > session_timeout


def _check_high_value_interaction(state: State) -> bool:
    """Check if interaction was high-value (complex reasoning/multiple tools)."""
    # High value indicators
    high_iterations = state.execution.iteration > 3
    multiple_tools = len(getattr(state.execution, "completed_calls", [])) > 2

    return high_iterations or multiple_tools


def _synthesis_in_progress(user_profile) -> bool:
    """Check if synthesis is already running to prevent duplicates."""
    return getattr(user_profile, "_synthesis_lock", False)


def _mark_synthesis_start(user_profile):
    """Mark synthesis as in progress."""
    user_profile._synthesis_lock = True
    user_profile._synthesis_start_time = datetime.now()


def _mark_synthesis_complete(user_profile):
    """Mark synthesis as complete."""
    user_profile._synthesis_lock = False
    user_profile.last_synthesis_count = user_profile.interaction_count
    user_profile.last_synthesis_time = datetime.now().isoformat()


async def _execute_synthesis(memory, user_id: str, user_profile, state: State):
    """Execute the actual synthesis process with LLM."""
    # Create interaction data from current state
    interaction_data = {
        "query": getattr(user_profile, "_current_query", "")
        or getattr(state.execution, "query", ""),
        "response": getattr(user_profile, "_current_response", "")
        or state.execution.response
        or "",
        "success": True,
        "timestamp": datetime.now().isoformat(),
    }

    # Use the new LLM-powered synthesis
    await _synthesize_with_llm(memory, user_id, user_profile, interaction_data, state)


async def _synthesize_with_llm(
    memory, user_id: str, user_profile, interaction_data: Dict[str, Any], state: State
):
    """Perform LLM-powered synthesis of user understanding."""
    try:
        # Build synthesis prompt
        prompt = build_synthesis_prompt(user_profile, interaction_data, state)

        # Get LLM synthesis
        from resilient_result import unwrap

        llm_result = await memory.llm.run([{"role": "user", "content": prompt}])
        llm_response = unwrap(llm_result)

        # Parse synthesis results
        synthesis_data = _parse_synthesis_response(llm_response)

        if synthesis_data:
            # Update user profile with synthesis results
            _apply_synthesis_to_profile(user_profile, synthesis_data)

            # Save updated profile
            if memory.store:
                await memory._save_profile(user_profile)

            emit(
                "synthesize",
                state="llm_complete",
                user_id=user_id,
                insights_count=len(synthesis_data),
            )
        else:
            emit("synthesize", state="llm_parse_error", user_id=user_id)

    except Exception as e:
        emit("synthesize", state="llm_error", user_id=user_id, error=str(e))
        # Fallback to basic update
        await memory.update_impression(user_id, interaction_data)


def _parse_synthesis_response(llm_response: str) -> Optional[Dict[str, Any]]:
    """Parse LLM synthesis response into structured data."""
    try:
        # Clean the response - remove any markdown formatting
        clean_response = llm_response.strip()
        if clean_response.startswith("```json"):
            clean_response = clean_response[7:]
        if clean_response.endswith("```"):
            clean_response = clean_response[:-3]

        # Parse JSON
        synthesis_data = json.loads(clean_response.strip())
        return synthesis_data

    except (json.JSONDecodeError, ValueError) as e:
        emit("synthesis_parse_error", error=str(e), response_preview=llm_response[:200])
        return None


def _apply_synthesis_to_profile(user_profile, synthesis_data: Dict[str, Any]):
    """Apply synthesis insights to user profile."""
    # Update preferences
    if "preferences" in synthesis_data:
        user_profile.preferences = {
            **(user_profile.preferences or {}),
            **synthesis_data["preferences"],
        }

    # Update goals (merge with existing)
    if "goals" in synthesis_data:
        existing_goals = set(user_profile.goals or [])
        new_goals = set(synthesis_data["goals"])
        user_profile.goals = list(existing_goals | new_goals)

    # Update expertise (merge with existing)
    if "expertise" in synthesis_data:
        existing_expertise = set(user_profile.expertise or [])
        new_expertise = set(synthesis_data["expertise"])
        user_profile.expertise = list(existing_expertise | new_expertise)

    # Update communication style
    if "communication_style" in synthesis_data:
        user_profile.communication_style = synthesis_data["communication_style"]

    # Store synthesis metadata
    user_profile.last_synthesis_time = datetime.now().isoformat()
    user_profile.synthesis_version = getattr(user_profile, "synthesis_version", 0) + 1
