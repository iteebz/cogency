"""Reason step - focused reasoning and decision making.

The reason step handles core cognitive processing:
- Focused reasoning on the current request
- Decision making for action selection
- Tool call planning and preparation
"""

import asyncio
from typing import Optional

from resilient_result import unwrap

from cogency.events import emit
from cogency.observe import observe
from cogency.providers import Provider
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
    llm: Provider,
    tools: list[Tool],
    memory,  # Impression instance or None
    identity: str = None,
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
        # Return response directly - identity already injected in reasoning
        emit("reason", state="direct_response", content=state.execution.response[:100])
        return state.execution.response

    return None
