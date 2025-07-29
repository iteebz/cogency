"""Act node - pure tool execution."""

import logging
import time
from typing import List

from cogency.decorators import phase
from cogency.phases.base import Phase

# Tool retry logic now handled by @safe.act() decorator
from cogency.state import State
from cogency.tools import Tool, run_tools

logger = logging.getLogger(__name__)


class Act(Phase):
    def __init__(self, tools):
        super().__init__(act, tools=tools)

    def next_phase(self, state: State) -> str:
        current_iter = state.iteration
        max_iter = state.depth
        stop_reason = state.stop_reason

        # Check stop conditions first
        if stop_reason in ["depth_reached", "reasoning_loop_detected"]:
            return "respond"
        elif current_iter >= max_iter:
            state.stop_reason = "depth_reached"
            return "respond"
        else:
            # Continue reasoning loop
            return "reason"


@phase.act()
async def act(state: State, notifier, tools: List[Tool]) -> None:
    """Act: execute tools based on reasoning decision."""
    time.time()

    tool_call_str = state.tool_calls
    if not tool_call_str:
        return  # State mutated in place

    # Direct access to state properties - no context wrapper needed
    selected_tools = state.selected_tools or tools

    # Tool calls come from reason node as parsed list
    tool_calls = state.tool_calls
    if not tool_calls or not isinstance(tool_calls, list):
        return  # State mutated in place

    # Start acting state
    # Acting is implicit - tool execution shows progress

    tool_tuples = [
        (call["name"], call["args"]) if isinstance(call, dict) else (call.name, call.args)
        for call in tool_calls
    ]

    # Let @safe.act() handle all tool execution errors, retries, and recovery
    tool_result = await run_tools(tool_tuples, selected_tools, state, notifier)

    # Tool result received - debug info available via state if needed

    # Store results using State methods (schema-compliant)
    if tool_result.success and tool_result.data:
        results_data = tool_result.data
        successes = results_data.get("results", [])
        failures = results_data.get("errors", [])

        # Processing tool results silently

        # Add successful tool results
        for success in successes:
            from cogency.types.tools import ToolOutcome

            state.add_tool_result(
                name=success["tool_name"],
                args=success["args"],
                result=str(success["result"]),
                outcome=ToolOutcome.SUCCESS,
            )

        # Add failed tool results
        for failure in failures:
            from cogency.types.tools import ToolOutcome

            state.add_tool_result(
                name=failure["tool_name"],
                args=failure["args"],
                result=failure.get("error", "Tool execution failed"),
                outcome=ToolOutcome.FAILURE,
            )

    # State mutated in place, no return needed
