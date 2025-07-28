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
        current_iter = state.iteration
        max_iter = state.max_iterations
        stop_reason = state.stop_reason

        # Check stop conditions first
        if stop_reason in ["max_iterations_reached", "reasoning_loop_detected"]:
            return "respond"
        elif current_iter >= max_iter:
            state.stop_reason = "max_iterations_reached"
            return "respond"
        else:
            # Continue reasoning loop
            return "reason"


# @robust.act()  # DISABLED FOR DEBUGGING
async def act(state: State, *, tools: List[BaseTool]) -> State:
    """Act: execute tools based on reasoning decision."""
    time.time()

    tool_call_str = state.tool_calls
    if not tool_call_str:
        return state

    context = state.context
    selected_tools = state.selected_tools or tools

    # Tool calls come from reason node as parsed list
    tool_calls = state.tool_calls
    if not tool_calls or not isinstance(tool_calls, list):
        return state

    # Start acting state
    # Acting is implicit - tool execution shows progress

    tool_tuples = [(call["name"], call["args"]) for call in tool_calls]

    # Let @safe.act() handle all tool execution errors, retries, and recovery
    tool_result = await run_tools(tool_tuples, selected_tools, context, state)
    
    # Store results using State methods (schema-compliant)
    if tool_result.success and tool_result.data:
        results_data = tool_result.data
        successes = results_data.get("results", [])
        failures = results_data.get("errors", [])
        
        # Add successful tool results
        for success in successes:
            from cogency.state import ToolOutcome
            state.add_tool_result(
                name=success["tool_name"],
                args=success["args"],
                result=str(success["result"]),
                outcome=ToolOutcome.SUCCESS
            )
        
        # Add failed tool results  
        for failure in failures:
            from cogency.state import ToolOutcome
            state.add_tool_result(
                name=failure["tool_name"],
                args=failure["args"],
                result=failure.get("error", "Tool execution failed"),
                outcome=ToolOutcome.FAILURE
            )

    return state
