"""State persistence utilities."""

from typing import Dict

from cogency.state.agent import State


async def _get_state(
    user_id: str,
    query: str,
    max_iterations: int,
    user_states: Dict[str, State],
    persistence=None,
) -> State:
    """Internal: Get existing state or restore from persistence, creating new if needed."""

    # Check existing in-memory state first
    state = user_states.get(user_id)
    if state:
        # Preserve conversation history from previous execution
        previous_messages = state.execution.messages

        # Reset for new query to prevent response caching
        state.query = query
        state.execution.iteration = 0
        state.execution.response = None
        state.execution.pending_calls.clear()
        state.execution.completed_calls.clear()
        state.execution.max_iterations = max_iterations
        state.execution.stop_reason = None

        # Restore conversation history
        state.execution.messages = previous_messages

        return state

    # Try to restore from persistence
    if persistence:
        state = await persistence.load(user_id)

        if state:
            # Update query for restored state
            state.query = query
            user_states[user_id] = state
            return state

    # Create new state if restore failed or persistence disabled
    state = State(query=query, user_id=user_id)
    state.execution.max_iterations = max_iterations
    user_states[user_id] = state
    return state
