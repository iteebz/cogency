"""Act node - pure tool execution."""

import logging
import time
from typing import List

from cogency.resilience import ActionError, recover, safe
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.tools.executor import run_tools
from cogency.utils.heuristics import calculate_backoff_delay, needs_network_retry
from cogency.utils.results import ActionResult

logger = logging.getLogger(__name__)


@safe.checkpoint("act")
@safe.act()
async def act(state: State, *, tools: List[BaseTool]) -> State:
    """Act: execute tools based on reasoning decision."""
    time.time()

    tool_call_str = state.tool_calls
    if not tool_call_str:
        state["action_result"] = ActionResult.ok(data={"type": "no_action"})
        return state

    context = state.context
    selected_tools = state.selected_tools or tools

    # Tool calls come from reason node as parsed list
    tool_calls = state.tool_calls
    if not tool_calls or not isinstance(tool_calls, list):
        state["action_result"] = ActionResult.ok(data={"type": "no_action"})
        return state

    # Start acting state
    # Acting is implicit - tool execution shows progress

    tool_tuples = [(call["name"], call["args"]) for call in tool_calls]

    # Network error recovery with backoff
    retry_count = state.network_retry_count
    max_retries = 2

    tool_execution_result = await run_tools(tool_tuples, selected_tools, context, state.output)

    if tool_execution_result.success:
        execution_results = ActionResult.ok(tool_execution_result.data)
    else:
        execution_results = ActionResult.fail(tool_execution_result.error)

    # Check for network errors that warrant retry
    if not execution_results.success and retry_count < max_retries:
        errors = [{"error": execution_results.error}] if execution_results.error else []

        if needs_network_retry(errors):
            import asyncio

            backoff_delay = calculate_backoff_delay(retry_count)
            await asyncio.sleep(backoff_delay)

            # Retry execution
            state["network_retry_count"] = retry_count + 1
            await state.output.trace(
                f"Network error detected, retrying in {backoff_delay}s (attempt {retry_count + 2})",
                node="act",
            )
            try:
                tool_execution_result = await run_tools(
                    tool_tuples, selected_tools, context, state.output
                )
                if tool_execution_result.success:
                    execution_results = ActionResult.ok(tool_execution_result.data)
                else:
                    execution_results = ActionResult.fail(tool_execution_result.error)
            except Exception as e:
                action_error = ActionError(
                    f"Tool execution failed: {str(e)}",
                    failed_tools=[call.get("name", "unknown") for call in tool_calls],
                    recoverable=True,
                )
                recovery = await recover.action(action_error, state)
                if recovery.success:
                    state.update(recovery.data)
                    execution_results = ActionResult.ok("Recovery attempted")
                else:
                    execution_results = ActionResult.fail(action_error.message)

    # Reset retry count on success or after max retries
    if execution_results.success or retry_count >= max_retries:
        state["network_retry_count"] = 0

    # Removed trace - clean tool output speaks for itself

    # Update flow state - routing handled by flow.py
    state["action_result"] = execution_results

    # Update cognition with formatted results after tool execution
    if execution_results.success and state.tool_calls and state.cognition.iterations:
        from cogency.nodes.reason import format_actions

        tool_calls = state.tool_calls
        formatted_result = format_actions(execution_results, tool_calls, selected_tools)
        # Update the last entry with formatted results
        state.cognition.update_result(formatted_result)

    # Note: current_iteration is incremented in reason.py, not here

    return state
