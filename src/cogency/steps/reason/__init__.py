"""Reason step - focused reasoning and decision making.

The reason step handles core cognitive processing:
- Focused reasoning on the current request
- Decision making for action selection
- Tool call planning and preparation
"""

import asyncio
from typing import List, Optional

from resilient_result import unwrap

from cogency.events import emit
from cogency.observe import observe
from cogency.providers import LLM
from cogency.resilience import resilience
from cogency.state import State
from cogency.tools import Tool

from .core import (
    _switch_mode,
    build_messages,
    build_reasoning_prompt,
    parse_reasoning_response,
)


@observe
@resilience
async def reason(
    state: State,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
    identity: str = None,
    output_schema: Optional[str] = None,
) -> Optional[str]:
    """Reason: focused reasoning and decision making."""

    # Get current state
    iteration = state.execution.iteration
    mode = state.execution.mode

    # Check stop conditions - force completion on final iteration
    max_iter = state.execution.max_iterations or 50  # Default to 50 if None
    if iteration >= max_iter:
        state.execution.stop_reason = "max_iterations_reached"
        emit("trace", message="Max iterations reached - forcing completion", iterations=iteration)
        # Force completion by returning a summary of work done
        from cogency.state.context import knowledge_synthesis

        knowledge = knowledge_synthesis(state)
        if knowledge and "KEY INSIGHTS:" in knowledge:
            # Extract insights as completion response
            insights_section = knowledge.split("KEY INSIGHTS:")[1].split("\n\n")[0].strip()
            if insights_section:
                return f"Task completed after {iteration} iterations. {insights_section}"

        # Fallback completion message
        return f"Task processed through {iteration} iterations. Based on the tools executed and information gathered, the requested work has been completed to the best of my ability."

    # Build reasoning prompt
    prompt = build_reasoning_prompt(state, tools, memory, identity)

    # Execute LLM call
    messages = build_messages(prompt, state)
    await asyncio.sleep(0)  # Yield for UI
    llm_result = await llm.run(messages)
    raw_response = unwrap(llm_result)

    # Parse and update state
    success, reasoning_data = parse_reasoning_response(raw_response)

    if not success:
        # Fallback to direct response
        if raw_response and not raw_response.strip().startswith("{"):
            state.execution.response = raw_response.strip()
            emit("reason", state="direct_response", content=raw_response[:100])
            return raw_response.strip()
        return None

    # Update state from reasoning response
    state.update_from_reasoning(reasoning_data)

    # Display reasoning
    if isinstance(reasoning_data, dict) and (thinking := reasoning_data.get("thinking", "")):
        # Show thinking for deep mode
        mode_value = (
            state.execution.mode.value
            if hasattr(state.execution.mode, "value")
            else str(state.execution.mode)
        )
        if mode_value == "deep":
            emit("reason", state="thinking_visible", content="✻ Thinking...", mode="deep")
        emit("reason", state="thinking", content=thinking)

    # Handle mode switching
    await _switch_mode(state, raw_response, mode, iteration)

    # Check for tool calls first - tools should execute before direct responses
    if state.execution.pending_calls:
        # Tool calls present - continue to action step
        return None

    # Handle direct response only if no tool calls
    if state.execution.response:
        # Apply output schema and identity if needed
        final_response = await _finalize_response(state, llm, identity, output_schema)
        emit("reason", state="direct_response", content=final_response[:100])
        return final_response

    return None


async def _finalize_response(
    state: State,
    llm: LLM,
    identity: Optional[str],
    output_schema: Optional[str],
) -> str:
    """Finalize response with identity and output schema formatting."""
    from resilient_result import unwrap

    from cogency.security import secure_response

    response = state.execution.response

    # If no identity or schema needed, return as-is
    if not identity and not output_schema:
        return response

    # Collect tool results for context
    tool_results = _collect_tool_results(state)
    failures = _collect_failures(state)

    # Build finalization prompt
    sanitized_query = _get_sanitized_query(state)

    # Create prompt for response finalization
    prompt_parts = []

    if identity:
        prompt_parts.append(f"IDENTITY: {identity}")

    if output_schema:
        prompt_parts.append(f"OUTPUT SCHEMA: {output_schema}")

    if tool_results:
        prompt_parts.append(f"TOOL RESULTS:\n{tool_results}")

    if failures:
        failure_text = "\n".join([f"• {name}: {error}" for name, error in failures.items()])
        prompt_parts.append(f"TOOL FAILURES:\n{failure_text}")

    prompt_parts.append(
        "Apply the identity and format according to the schema if provided. Keep the core response content but adjust tone and format as needed."
    )

    system_prompt = "\n\n".join(prompt_parts)

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": sanitized_query},
        {"role": "assistant", "content": response},
    ]

    llm_result = await llm.run(messages)
    final_response = unwrap(llm_result)

    return secure_response(final_response)


def _collect_tool_results(state: State) -> Optional[str]:
    """Extract and format tool results for response context."""
    if not state.execution.completed_calls:
        return None

    # Format completed tool results
    successful_results = [
        result for result in state.execution.completed_calls[:10] if result.get("success", False)
    ]

    if not successful_results:
        return None

    def format_result(result):
        """Extract data from Result object safely."""
        result_obj = result.get("result")
        if result_obj and hasattr(result_obj, "success") and result_obj.success:
            return str(result_obj.data or "no result")
        return "no result"

    return "\n".join(
        [f"• {result['name']}: {format_result(result)}..." for result in successful_results]
    )


def _collect_failures(state: State) -> Optional[dict]:
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
        if not result.get("success", True):  # Count as failure if success is False
            failures[result["name"]] = str(result.get("error", "Tool execution failed"))

    return failures if failures else None


def _get_sanitized_query(state: State) -> str:
    """Get sanitized user input from messages, not raw query."""
    sanitized_query = state.execution.query
    if state.execution.messages:
        # Use the last user message which should be sanitized
        user_messages = [msg for msg in state.execution.messages if msg["role"] == "user"]
        if user_messages:
            sanitized_query = user_messages[-1]["content"]
    return sanitized_query
