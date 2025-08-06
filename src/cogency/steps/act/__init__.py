"""Tool execution."""

import logging
from typing import List, Optional

from cogency.state import AgentState
from cogency.tools import Tool

from .execute import execute_tools

logger = logging.getLogger(__name__)


async def act(state: AgentState, llm=None, tools: List[Tool] = None) -> Optional[str]:
    """Act: execute tools based on reasoning decision."""

    # Check pending calls
    if not state.execution.pending_calls:
        return None

    # Check tools
    if not tools:
        return None

    tool_calls = state.execution.pending_calls
    if not isinstance(tool_calls, list):
        return None

    # Prepare tool tuples
    tool_tuples = [
        (call["name"], call["args"]) if isinstance(call, dict) else (call.name, call.args)
        for call in tool_calls
    ]

    # Execute tools
    tool_result = await execute_tools(tool_tuples, tools, state)

    # Handle results
    if tool_result.success and tool_result.data:
        results_data = tool_result.data
        successes = results_data.get("results", [])
        failures = results_data.get("errors", [])

        # Complete results
        completed_results = successes + failures
        state.execution.complete_tool_calls(completed_results)

    return None
