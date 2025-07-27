"""Act node - pure tool execution."""

import logging
import time
from typing import List

# Tool retry logic now handled by @safe.act() decorator
from resilient_result import Result

from cogency.nodes.base import Node
from cogency.resilience import robust
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.executor import run_tools

logger = logging.getLogger(__name__)


class Act(Node):
    def __init__(self, **kwargs):
        super().__init__(act, **kwargs)

    def next_node(self, state: State) -> str:
        execution_results = state.result
        current_iter = state.iteration
        max_iter = state.max_iterations
        stop_reason = state.stop_reason

        if stop_reason in ["max_iterations_reached", "reasoning_loop_detected"]:
            return "respond"
        elif current_iter >= max_iter:
            state["stop_reason"] = "max_iterations_reached"
            return "respond"
        elif not execution_results.success:
            failed_attempts = state.tool_failures
            if failed_attempts >= 3:
                state["stop_reason"] = "repeated_tool_failures"
                return "respond"
            else:
                state["tool_failures"] = failed_attempts + 1
                return "reason"
        else:
            from cogency.nodes.reasoning.adaptive import assess_tools

            tool_quality = assess_tools(execution_results)
            quality_attempts = state.quality_retries

            if tool_quality in ["failed", "poor"] and quality_attempts < 2:
                state["quality_retries"] = quality_attempts + 1
                return "reason"
            else:
                state["quality_retries"] = 0
                state["tool_failures"] = 0
                return "reason"


# @robust.act()  # DISABLED FOR DEBUGGING
async def act(state: State, *, tools: List[BaseTool]) -> State:
    """Act: execute tools based on reasoning decision."""
    time.time()

    tool_call_str = state.tool_calls
    if not tool_call_str:
        state["result"] = Result.ok(data={"type": "no_action"})
        return state

    context = state.context
    selected_tools = state.selected_tools or tools

    # Tool calls come from reason node as parsed list
    tool_calls = state.tool_calls
    if not tool_calls or not isinstance(tool_calls, list):
        state["result"] = Result.ok(data={"type": "no_action"})
        return state

    # Start acting state
    # Acting is implicit - tool execution shows progress

    tool_tuples = [(call["name"], call["args"]) for call in tool_calls]

    # Let @safe.act() handle all tool execution errors, retries, and recovery
    tool_result = await run_tools(tool_tuples, selected_tools, context, state)
    results = Result.ok(tool_result.data)

    # Removed trace - clean tool output speaks for itself

    # Update flow state - routing handled by flow.py
    state["result"] = results

    # Update cognition with formatted results after tool execution
    if results.success and state.tool_calls and state.iterations:
        from cogency.nodes.reason import format_actions

        tool_calls = state.tool_calls
        formatted_result = format_actions(results, tool_calls, selected_tools)
        # Update the last entry with formatted results
        state.update_result(formatted_result)

    # Note: iteration is incremented in reason.py, not here

    return state
