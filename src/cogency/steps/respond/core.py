"""Core response functions - consolidated business logic."""

import re
from typing import Dict, Optional

from resilient_result import Result, unwrap

from cogency.providers import LLM
from cogency.state import AgentState

from .prompt import prompt_response


def collect_tool_results(state: AgentState) -> Optional[str]:
    """Extract and format tool results for response context."""
    if not state.execution.completed_calls:
        return None

    # Format completed tool results
    successful_results = [
        result for result in state.execution.completed_calls[:5] if "result" in result
    ]

    if not successful_results:
        return None

    return "\n".join(
        [
            f"• {result['name']}: {str(result['result'] or 'no result')[:200]}..."
            for result in successful_results
        ]
    )


def collect_failures(state: AgentState) -> Optional[Dict[str, str]]:
    """Collect all failure scenarios into unified dict."""
    failures = {}

    # Check for stop reason (reasoning failures)
    if state.execution.stop_reason:
        user_error_message = getattr(
            state, "user_error_message", "I encountered an issue but will try to help."
        )
        failures["reasoning"] = user_error_message
        return failures

    # Check for tool failures in completed calls
    for result in state.execution.completed_calls:
        if (
            "result" in result
            and result["result"]
            and hasattr(result["result"], "success")
            and not result["result"].success
        ):
            failures[result["name"]] = str(result["result"].error) or "Tool execution failed"

    return failures if failures else None


def has_existing_response(state: AgentState) -> bool:
    """Check if state has an existing response."""
    return bool(state.execution.response)


def extract_existing_response(state: AgentState) -> str:
    """Extract and unwrap existing response from state."""
    if isinstance(state.execution.response, Result):
        return unwrap(state.execution.response)
    else:
        return state.execution.response


def get_sanitized_query(state: AgentState) -> str:
    """Get sanitized user input from messages, not raw query."""
    sanitized_query = state.execution.query
    if state.execution.messages:
        # Use the last user message which should be sanitized
        user_messages = [msg for msg in state.execution.messages if msg["role"] == "user"]
        if user_messages:
            sanitized_query = user_messages[-1]["content"]
    return sanitized_query


async def apply_security_check(response: str) -> str:
    """Apply security assessment and redaction to response."""
    from cogency.security import SecurityAction, assess

    security_result = await assess(response)
    if security_result.action == SecurityAction.BLOCK:
        raise ValueError("Security violation: Output contains unsafe content")
    elif security_result.action == SecurityAction.REDACT:
        # Apply redaction patterns
        response = re.sub(r"sk-[a-zA-Z0-9]{32,}", "[REDACTED]", response)
        response = re.sub(r"AKIA[a-zA-Z0-9]{16}", "[REDACTED]", response)
    return response


async def apply_identity(
    state: AgentState,
    llm: LLM,
    identity: str,
    tool_results: Optional[str],
    output_schema: Optional[str],
) -> str:
    """Apply agent identity to existing response via LLM call."""
    sanitized_query = get_sanitized_query(state)

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

    llm_result = await llm.run(messages)
    response = unwrap(llm_result)
    return await apply_security_check(response)


async def generate_new_response(
    state: AgentState,
    llm: LLM,
    tool_results: Optional[str],
    failures: Optional[Dict[str, str]],
    identity: Optional[str],
    output_schema: Optional[str],
) -> str:
    """Generate response from available tool results and context."""
    sanitized_query = get_sanitized_query(state)

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

    llm_result = await llm.run(messages)
    response = unwrap(llm_result)
    return await apply_security_check(response)
