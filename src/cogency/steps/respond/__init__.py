"""Respond step - response generation and formatting.

The respond step handles final response creation:
- Response generation from context and tool results
- Identity and personality application
- Output schema formatting and validation

Internal functions handle tool result collection and identity shaping.
"""

from typing import List, Optional

from cogency.providers import LLM
from cogency.state import AgentState
from cogency.tools import Tool

from .format import collect_failures, format_tool_results
from .generate import extract_existing_response, generate_response_from_context, shape_identity


async def respond(
    state: AgentState,
    notifier,
    llm: LLM,
    tools: List[Tool],
    memory=None,  # Impression instance or None
    identity: Optional[str] = None,
    output_schema: Optional[str] = None,
) -> None:
    """Respond: generate final formatted response with personality."""
    await notifier("respond", state="generating")

    # Collect tool results for conditional identity prompting
    tool_results = format_tool_results(state)

    # Route to appropriate response generation strategy
    if (
        state.execution.response
        and hasattr(state.execution, "response_source")
        and state.execution.response_source in ["triage", "reason"]
        and identity
    ):
        # Apply identity via LLM call for early returns
        response_text = await shape_identity(state, llm, identity, tool_results, output_schema)
    elif state.execution.response:
        # Use existing response without identity
        response_text = extract_existing_response(state)
    else:
        # Generate response from available context
        failures = collect_failures(state)

        if tool_results or failures:
            response_text = await generate_response_from_context(
                state, llm, identity, output_schema, tool_results, failures
            )
        else:
            # True fallback - no context available
            response_text = "I'm here to help. How can I assist you?"

    await notifier("respond", state="complete", content=(response_text or "")[:100])

    # Update state
    state.execution.add_message("assistant", response_text)
    # Always update response with final processed text (may include identity)
    state.execution.response = response_text
    return state
