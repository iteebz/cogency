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

from .core import filter_tools, notify_tool_selection, triage_prompt


async def triage(
    state: AgentState,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
) -> Optional[str]:
    """Triage: routing decisions, memory extraction, tool selection."""

    # Route and filter
    query = state.execution.query
    result = await triage_prompt(llm, query, tools)

    # Handle direct response (early return)
    if result.direct_response:
        state.execution.response = result.direct_response
        return result.direct_response

    # Select tools
    filtered_tools = filter_tools(tools, result.selected_tools)

    # Update state
    state.execution.mode = result.mode
    state.execution.iteration = 0

    # Notify results
    await notify_tool_selection(filtered_tools, len(tools))

    return None  # Continue to reason step
