"""State persistence utilities - Clean helpers for agent integration."""

from typing import Dict

from cogency.state import AgentState


async def get_state(
    user_id: str,
    query: str,
    depth: int,
    user_states: Dict[str, AgentState],
    persistence=None,
) -> AgentState:
    """Get existing state or restore from persistence, creating new if needed."""

    # Check existing in-memory state first
    state = user_states.get(user_id)
    if state:
        state.execution.query = query
        return state

    # Try to restore from persistence
    if persistence:
        state = await persistence.load(user_id)

        if state:
            # Update query for restored state
            state.execution.query = query
            user_states[user_id] = state
            return state

    # Create new state if restore failed or persistence disabled
    state = AgentState(query=query, user_id=user_id)
    state.execution.max_iterations = depth
    user_states[user_id] = state
    return state
