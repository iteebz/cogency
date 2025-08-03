"""Tool execution."""

import logging
from typing import List, Optional

from cogency.state import AgentState
from cogency.tools import Tool

from .executor import execute_tools

logger = logging.getLogger(__name__)


async def act(state: AgentState, notifier, tools: List[Tool]) -> Optional[str]:
    """Execute tools based on reasoning decision."""
    # Check if there are pending tool calls
    if not state.execution.pending_calls:
        return None

    tool_calls = state.execution.pending_calls
    if not isinstance(tool_calls, list):
        return None

    tool_tuples = [
        (call["name"], call["args"]) if isinstance(call, dict) else (call.name, call.args)
        for call in tool_calls
    ]

    # Execute tools with error isolation - execute_tools handles all tool execution
    # errors, retries, and recovery by wrapping results in Result objects
    tool_result = await execute_tools(tool_tuples, tools, state, notifier)

    # Store results using ExecutionState methods
    if tool_result.success and tool_result.data:
        results_data = tool_result.data
        successes = results_data.get("results", [])
        failures = results_data.get("errors", [])

        # Prepare results for completion
        completed_results = []

        for success in successes:
            completed_results.append(
                {
                    "name": success["tool_name"],
                    "args": success["args"],
                    "result": success["result_object"],
                }
            )

        for failure in failures:
            completed_results.append(
                {
                    "name": failure["tool_name"],
                    "args": failure["args"],
                    "result": failure["result_object"],
                }
            )

        # Complete the tool calls
        state.execution.complete_tool_calls(completed_results)

    return None
