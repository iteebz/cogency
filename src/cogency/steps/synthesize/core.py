"""Core synthesis orchestrator - clean and focused."""

from datetime import datetime
from typing import Any, Dict

from cogency.events import emit
from cogency.state import State

from .archival import process_archival_insights
from .profile import apply_synthesis_to_profile, parse_synthesis_response
from .prompt import build_synthesis_prompt
from .triggers import (
    mark_synthesis_complete,
    mark_synthesis_start,
    should_synthesize,
    synthesis_in_progress,
)


async def synthesize(state: State, memory) -> None:
    """Synthesis step - consolidates memory based on triggers."""
    if not memory:
        return

    emit("synthesize", state="start", user_id=state.user_id)

    # Check synthesis triggers
    user_profile = state.profile or await memory._load_profile(state.user_id)

    if not should_synthesize(user_profile, state):
        emit("synthesize", state="skipped", reason="no_trigger")
        return

    # Check idempotence - prevent duplicate synthesis
    if synthesis_in_progress(user_profile):
        emit("synthesize", state="skipped", reason="already_running")
        return

    try:
        # Mark synthesis in progress
        mark_synthesis_start(user_profile)

        # Async synthesis to prevent blocking
        emit("synthesize", state="executing", synthesis_type="async")
        await _execute_synthesis(memory, state.user_id, user_profile, state)

        emit("synthesize", state="complete", user_id=state.user_id)

    except Exception as e:
        emit("synthesize", state="error", error=str(e))
        # Synthesis failures don't affect user experience
    finally:
        mark_synthesis_complete(user_profile)


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
        prompt = build_synthesis_prompt(interaction_data, state)

        # Get LLM synthesis
        from resilient_result import unwrap

        llm_result = await memory.provider.run([{"role": "user", "content": prompt}])
        response = unwrap(llm_result)

        # Parse synthesis results
        synthesis_data = parse_synthesis_response(response)

        if synthesis_data:
            # Update user profile with synthesis results
            profile_data = synthesis_data.get("profile", synthesis_data)  # Backward compatibility
            apply_synthesis_to_profile(user_profile, profile_data)

            # Process archival insights if present
            archival_insights = synthesis_data.get("archival", [])
            if archival_insights and memory.archival:
                await process_archival_insights(memory.archival, user_id, archival_insights)

            # Save updated profile
            if memory.store:
                await memory._save_profile(user_profile)

            emit(
                "synthesize",
                state="llm_complete",
                user_id=user_id,
                profile_insights_count=len(profile_data),
                archival_insights_count=len(archival_insights),
            )
        else:
            emit("synthesize", state="llm_parse_error", user_id=user_id)

    except Exception as e:
        emit("synthesize", state="llm_error", user_id=user_id, error=str(e))
        # Fallback to basic update
        await memory.update_impression(user_id, interaction_data)