"""Triage step - routing, memory extraction, tool filtering.

The triage step handles initial request processing:
- Routing decisions for request type
- Memory extraction and context building
- Tool selection and filtering
"""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import AgentState
from cogency.tools import Tool

from .core import MemoryResult, filter_tools, notify_tool_selection, save_memory, unified_triage


async def triage(
    state: AgentState,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
) -> Optional[str]:
    """Triage: routing decisions, memory extraction, tool selection."""

    # Route and filter
    query = state.execution.query
    result = await unified_triage(llm, query, tools)

    # Handle direct response (early return)
    if result.direct_response:
        state.execution.response = result.direct_response
        return result.direct_response

    # Extract memory
    if result.memory_content and memory:
        memory_result = MemoryResult(
            content=result.memory_content, tags=result.memory_tags, memory_type="fact"
        )
        await save_memory(memory_result, memory)

    # Select tools
    filtered_tools = filter_tools(tools, result.selected_tools)

    # Update state
    state.execution.mode = result.mode
    state.execution.iteration = 0

    # Notify results
    await notify_tool_selection(filtered_tools, len(tools))

    return None  # Continue to reason step
