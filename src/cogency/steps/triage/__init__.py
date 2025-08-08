"""Triage step - routing, memory extraction, tool filtering.

The triage step handles initial request processing:
- Routing decisions for request type
- Memory extraction and context building
- Tool selection and filtering
"""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import State
from cogency.tools import Tool

from .core import filter_tools, notify_tool_selection, triage_prompt


async def triage(
    state: State,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
    identity: str = None,
) -> Optional[str]:
    """Triage: routing decisions, memory extraction, tool selection."""

    # Route and filter
    from cogency.state.mutations import get_situated_context

    query = state.query  # CANONICAL: query is at top level in Three-Horizon model
    user_context = get_situated_context(state)
    result = await triage_prompt(llm, query, tools, user_context, identity)

    # Handle direct response (early return)
    if result.direct_response:
        state.execution.response = result.direct_response
        return result.direct_response

    # Check if tools are requested but none available
    if result.selected_tools and not tools:
        state.execution.response = "I don't have access to any tools to help with this request. I can only provide direct responses based on my knowledge."
        return state.execution.response

    # Select tools
    filtered_tools = filter_tools(tools, result.selected_tools)

    # Update state
    state.execution.mode = result.mode
    state.execution.iteration = 0

    # Notify results
    await notify_tool_selection(filtered_tools, len(tools))

    return None  # Continue to reason step
