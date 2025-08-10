"""Synthesis trigger logic - when to consolidate memory."""

from datetime import datetime
from typing import Any, Dict

from cogency.state import State


def should_synthesize(user_profile, state: State) -> bool:
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


def synthesis_in_progress(user_profile) -> bool:
    """Check if synthesis is already running to prevent duplicates."""
    return getattr(user_profile, "_synthesis_lock", False)


def mark_synthesis_start(user_profile):
    """Mark synthesis as in progress."""
    user_profile._synthesis_lock = True
    user_profile._synthesis_start_time = datetime.now()


def mark_synthesis_complete(user_profile):
    """Mark synthesis as complete."""
    user_profile._synthesis_lock = False
    user_profile.last_synthesis_count = user_profile.interaction_count
    user_profile.last_synthesis_time = datetime.now().isoformat()