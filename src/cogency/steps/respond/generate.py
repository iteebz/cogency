"""LLM response generation logic."""

from typing import Dict, Optional

from cogency.providers import LLM
from cogency.state import AgentState

from .prompts import prompt_response


async def shape_identity(
    state: AgentState,
    llm: LLM,
    identity: str,
    tool_results: Optional[str],
    output_schema: Optional[str],
) -> str:
    """Apply agent identity to existing response via LLM call.
    
    SEC-001: Use sanitized query to prevent prompt injection in identity shaping.
    """
    # SEC-001: Get sanitized user input from messages, not raw query
    sanitized_query = state.execution.query
    if state.execution.messages:
        # Use the last user message which should be sanitized
        user_messages = [msg for msg in state.execution.messages if msg["role"] == "user"]
        if user_messages:
            sanitized_query = user_messages[-1]["content"]
    
    identity_prompt = prompt_response(
        sanitized_query,
        has_tool_results=bool(tool_results),
        tool_summary=tool_results,
        identity=identity,
        output_schema=output_schema,
    )

    messages = [
        {"role": "system", "content": identity_prompt},
        {"role": "user", "content": sanitized_query},
        {"role": "assistant", "content": state.execution.response},
    ]

    from resilient_result import unwrap
    from cogency.security import sanitize_output

    llm_result = await llm.run(messages)
    response = unwrap(llm_result)
    # SEC-003: Sanitize output to prevent information leakage
    return sanitize_output(response)


async def generate_response_from_context(
    state: AgentState,
    llm: LLM,
    identity: Optional[str],
    output_schema: Optional[str],
    tool_results: Optional[str],
    failures: Optional[Dict[str, str]],
) -> str:
    """Generate response from available tool results and context.
    
    SEC-001: Use sanitized query to prevent prompt injection in response generation.
    """
    # SEC-001: Get sanitized user input from messages, not raw query
    sanitized_query = state.execution.query
    if state.execution.messages:
        # Use the last user message which should be sanitized
        user_messages = [msg for msg in state.execution.messages if msg["role"] == "user"]
        if user_messages:
            sanitized_query = user_messages[-1]["content"]
    
    response_prompt = prompt_response(
        sanitized_query,
        has_tool_results=bool(tool_results),
        tool_summary=tool_results,
        identity=identity,
        output_schema=output_schema,
        failures=failures,
    )

    messages = [
        {"role": "system", "content": response_prompt},
        {"role": "user", "content": sanitized_query},
    ]

    from resilient_result import unwrap
    from cogency.security import sanitize_output

    llm_result = await llm.run(messages)
    response = unwrap(llm_result)
    # SEC-003: Sanitize output to prevent information leakage
    return sanitize_output(response)


def extract_existing_response(state: AgentState) -> str:
    """Extract and unwrap existing response from state."""
    from resilient_result import Result, unwrap

    if isinstance(state.execution.response, Result):
        return unwrap(state.execution.response)
    else:
        return state.execution.response
