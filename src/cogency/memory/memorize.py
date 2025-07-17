"""Memory-related nodes for the cognitive workflow."""
from typing import Optional

from cogency.memory.core import MemoryBackend
from cogency.common.types import AgentState
from cogency.utils.tracing import trace_node


@trace_node("memorize")
async def memorize_node(state: AgentState, *, memory: MemoryBackend) -> AgentState:
    """Memorize content if it meets certain criteria."""
    query = state["query"]
    context = state["context"]
    user_id = getattr(context, 'user_id', 'default')
    
    if hasattr(memory, 'should_store'):
        should_store, category = memory.should_store(query)
        if should_store:
            await memory.memorize(query, tags=[category], user_id=user_id)
    return state
