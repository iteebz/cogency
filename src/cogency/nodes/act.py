"""Act node - pure tool execution."""

import logging
import time
from typing import List

from cogency.resilience import safe
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.executor import run_tools

# Tool retry logic now handled by @safe.act() decorator
from cogency.utils.results import Result

logger = logging.getLogger(__name__)


@safe.checkpoint("act")
@safe.act()
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
    tool_result = await run_tools(tool_tuples, selected_tools, context, state.output)
    results = Result.ok(tool_result.data)

    # Removed trace - clean tool output speaks for itself

    # Update flow state - routing handled by flow.py
    state["result"] = results

    # Update cognition with formatted results after tool execution
    if results.success and state.tool_calls and state.cognition.iterations:
        from cogency.nodes.reason import format_actions

        tool_calls = state.tool_calls
        formatted_result = format_actions(results, tool_calls, selected_tools)
        # Update the last entry with formatted results
        state.cognition.update_result(formatted_result)

    # Note: iteration is incremented in reason.py, not here

    return state
