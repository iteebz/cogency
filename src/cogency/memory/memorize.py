"""Memory-related nodes for the cognitive workflow."""
from typing import Optional

from cogency.memory.base import BaseMemory
from cogency.common.types import AgentState
from cogency.utils.tracing import trace_node


@trace_node("memorize")
async def memorize_node(state: AgentState, *, memory: BaseMemory) -> AgentState:
    """Memorize content if it meets certain criteria."""
    query = state["query"]
    if hasattr(memory, 'should_store'):
        should_store, category = memory.should_store(query)
        if should_store:
            await memory.memorize(query, tags=[category])
    return state
