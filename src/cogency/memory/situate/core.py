"""Core situated memory logic - profile updates and context injection."""

from datetime import datetime
from typing import Any

from cogency.events import emit
from cogency.state import State


async def situate(state: State, memory) -> None:
    """Update user profile with conversation impressions."""
    if not memory:
        return

    emit("situate", state="start", user_id=state.user_id)

    # Check synthesis triggers
    user_profile = state.profile or await memory._load_profile(state.user_id)

    if not _should_situate(user_profile, state):
        emit("situate", state="skipped", reason="no_trigger")
        return

    # Check idempotence - prevent duplicate synthesis
    if _situate_in_progress(user_profile):
        emit("situate", state="skipped", reason="already_running")
        return

    try:
        # Mark situate in progress
        _mark_situate_start(user_profile)

        # Async situate to prevent blocking
        emit("situate", state="executing", synthesis_type="async")
        await _execute_situate(memory, state.user_id, user_profile, state)

        emit("situate", state="complete", user_id=state.user_id)

    except Exception as e:
        emit("situate", state="error", error=str(e))
        # Situate failures don't affect user experience
    finally:
        _mark_situate_complete(user_profile)


def _should_situate(user_profile, state: State) -> bool:
    """Check if profile update should trigger."""
    # Semantic trigger from triage (queued async)
    if hasattr(state, "_situate_queued"):
        return True

    # Fallback: 24-hour ceiling or emergency high threshold
    from datetime import datetime, timedelta

    last_update = getattr(user_profile, "last_updated", None)
    if last_update and (datetime.now() - last_update) > timedelta(hours=24):
        return True

    # Emergency fallback: very high interaction threshold
    return (user_profile.interaction_count % 50) == 0


def _situate_in_progress(user_profile) -> bool:
    """Check if profile update is already in progress."""
    return getattr(user_profile, "_situate_in_progress", False)


def _mark_situate_start(user_profile):
    """Mark profile update as in progress."""
    user_profile._situate_in_progress = True


def _mark_situate_complete(user_profile):
    """Mark profile update as complete."""
    user_profile._situate_in_progress = False


async def _execute_situate(memory, user_id: str, user_profile, state: State):
    """Execute the actual profile update process with LLM."""
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

    # Use the new LLM-powered profile update
    await _situate_with_llm(memory, user_id, user_profile, interaction_data, state)


async def _situate_with_llm(
    memory, user_id: str, user_profile, interaction_data: dict[str, Any], state: State
):
    """Perform LLM-powered synthesis of user understanding."""
    from .profile import apply_synthesis_to_profile, parse_synthesis_response
    from .prompt import build_synthesis_prompt

    try:
        # Build synthesis prompt
        prompt = build_synthesis_prompt(interaction_data, state)

        # Get LLM synthesis
        from resilient_result import unwrap

        llm_result = await memory.provider.run([{"role": "user", "content": prompt}])
        response = unwrap(llm_result)

        # Parse synthesis results
        synthesis_data = parse_synthesis_response(response)

        if synthesis_data:
            # Update user profile with synthesis results (profile only)
            apply_synthesis_to_profile(user_profile, synthesis_data)

            # Save updated profile
            if memory.store:
                await memory._save_profile(user_profile)

            emit(
                "situate",
                state="llm_complete",
                user_id=user_id,
                profile_impressions_count=len(synthesis_data),
            )
        else:
            emit("situate", state="llm_parse_error", user_id=user_id)

    except Exception as e:
        emit("situate", state="llm_error", user_id=user_id, error=str(e))
        # Fallback to basic update
        await memory.update_impression(user_id, interaction_data)
