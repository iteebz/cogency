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
    """Apply agent identity to existing response via LLM call."""
    identity_prompt = prompt_response(
        state.execution.query,
        has_tool_results=bool(tool_results),
        tool_summary=tool_results,
        identity=identity,
        output_schema=output_schema,
    )

    messages = [
        {"role": "system", "content": identity_prompt},
        {"role": "user", "content": state.execution.query},
        {"role": "assistant", "content": state.execution.response},
    ]

    from resilient_result import unwrap

    llm_result = await llm.run(messages)
    return unwrap(llm_result)


async def generate_response_from_context(
    state: AgentState,
    llm: LLM,
    identity: Optional[str],
    output_schema: Optional[str],
    tool_results: Optional[str],
    failures: Optional[Dict[str, str]],
) -> str:
    """Generate response from available tool results and context."""
    response_prompt = prompt_response(
        state.execution.query,
        has_tool_results=bool(tool_results),
        tool_summary=tool_results,
        identity=identity,
        output_schema=output_schema,
        failures=failures,
    )

    messages = [
        {"role": "system", "content": response_prompt},
        {"role": "user", "content": state.execution.query},
    ]

    from resilient_result import unwrap

    llm_result = await llm.run(messages)
    return unwrap(llm_result)


def extract_existing_response(state: AgentState) -> str:
    """Extract and unwrap existing response from state."""
    from resilient_result import Result, unwrap

    if isinstance(state.execution.response, Result):
        return unwrap(state.execution.response)
    else:
        return state.execution.response
