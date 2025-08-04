"""Respond step - response generation and formatting.

The respond step handles final response creation:
- Response generation from context and tool results
- Identity and personality application
- Output schema formatting and validation
"""

from typing import List, Optional

from cogency.events import emit
from cogency.providers import LLM
from cogency.state import AgentState
from cogency.tools import Tool

from .core import (
    apply_identity,
    collect_failures,
    collect_tool_results,
    extract_existing_response,
    generate_new_response,
    has_existing_response,
)


async def respond(
    state: AgentState,
    llm: LLM,
    tools: List[Tool],
    memory=None,  # Impression instance or None
    identity: Optional[str] = None,
    output_schema: Optional[str] = None,
) -> None:
    """Respond: generate final formatted response."""
    emit("respond", level="debug", state="generating")

    # Collect context
    tool_results = collect_tool_results(state)
    failures = collect_failures(state)

    # Choose strategy
    if has_existing_response(state) and identity:
        response_text = await apply_identity(state, llm, identity, tool_results, output_schema)
    elif has_existing_response(state):
        response_text = extract_existing_response(state)
    else:
        if tool_results or failures:
            response_text = await generate_new_response(
                state, llm, tool_results, failures, identity, output_schema
            )
        else:
            # True fallback - no context available
            response_text = "I'm here to help. How can I assist you?"

    # Update state
    state.execution.add_message("assistant", response_text)
    state.execution.response = response_text

    emit("respond", state="complete", content=(response_text or "")[:100])
    return state
