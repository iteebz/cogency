"""State persistence utilities - Clean helpers for agent integration."""

from typing import Optional, Dict, Any
from cogency.state import State


async def get_state(
    user_id: str,
    query: str,
    max_iterations: int,
    user_states: Dict[str, State],
    persistence_manager = None,
    llm = None
) -> State:
    """Get existing state or restore from persistence, creating new if needed."""
    
    # Check existing in-memory state first
    state = user_states.get(user_id)
    if state:
        state.query = query
        return state
    
    # Try to restore from persistence
    if persistence_manager:
        state = await persistence_manager.load_state(
            user_id,
            validate_llm=True,
            expected_llm_provider=getattr(llm, 'provider', None),
            expected_llm_model=getattr(llm, 'model', None)
        )
        
        if state:
            # Update query for restored state
            state.query = query
            user_states[user_id] = state
            return state
    
    # Create new state if restore failed or persistence disabled
    state = State(query=query, user_id=user_id, max_iterations=max_iterations)
    user_states[user_id] = state
    return state