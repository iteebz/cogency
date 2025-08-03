"""Reason step - focused reasoning and decision making.

The reason step handles core cognitive processing:
- Focused reasoning on the current request
- Decision making for action selection
- Tool call planning and preparation
"""

import asyncio
from typing import List, Optional

from resilient_result import unwrap

from cogency.providers import LLM
from cogency.state import AgentState
from cogency.tools import Tool

from .core import (
    build_messages,
    build_reasoning_prompt,
    handle_mode_switching,
    parse_reasoning_response,
)


async def reason(
    state: AgentState,
    notifier,
    llm: LLM,
    tools: List[Tool],
    memory,  # Impression instance or None
) -> Optional[str]:
    """Reason: focused reasoning and decision making."""

    # Get current state
    iteration = state.execution.iteration
    mode = state.execution.mode

    await notifier("reason", state=mode)

    # Check stop conditions
    if iteration >= state.execution.max_iterations:
        state.execution.stop_reason = "max_iterations_reached"
        await notifier("trace", message="Max iterations reached", iterations=iteration)
        return None

    # Build reasoning prompt
    prompt = build_reasoning_prompt(state, tools, memory)

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
            await notifier("reason", state="direct_response", content=raw_response[:100])
            return raw_response.strip()
        return None

    # Update state from reasoning response
    state.update_from_reasoning(reasoning_data)

    # Display reasoning
    if thinking := reasoning_data.get("thinking", ""):
        await notifier("reason", state="thinking", content=thinking)

    # Handle mode switching
    await handle_mode_switching(state, raw_response, mode, iteration, notifier)

    # Handle response types
    if state.execution.response:
        await notifier("reason", state="direct_response", content=state.execution.response[:100])
        return state.execution.response

    return None
