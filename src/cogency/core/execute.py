"""Tool execution - pure tool running logic."""

import json
import time

from ..lib.resilience import resilient_save
from .protocols import Event
from .result import Err, Ok, Result


async def execute_tools(calls: list, config, user_id: str = None) -> list[str]:
    """Execute tool call array sequentially - returns individual results."""
    results = []
    for call in calls:
        result = await _execute(call, config, user_id)
        if result.failure:
            # Store error as result instead of raising - errors go in "result" field
            results.append(result.error)
        else:
            results.append(result.unwrap())

    return results


async def execute(calls, config, user_id, conversation_id):
    """Execute tools and save results."""
    # Execute tools
    individual_results = await execute_tools(calls, config, user_id)

    # Create and save results event
    results_event = {
        "type": Event.RESULTS,
        "content": json.dumps(individual_results),
        "results": individual_results,
        "timestamp": time.time(),
    }
    resilient_save(
        conversation_id,
        user_id,
        Event.RESULTS,
        results_event["content"],
        results_event["timestamp"],
    )

    return individual_results, results_event


async def _execute(call: dict, config, user_id: str = None) -> Result[str]:
    """Execute single JSON call - pure function."""
    if not isinstance(call, dict):
        return Err("Call must be JSON object")

    tool_name = call.get("name")
    if not tool_name:
        return Err("Call missing 'name' field")

    # Find tool in list from config
    tool = next((t for t in config.tools if t.name == tool_name), None)
    if not tool:
        return Err(f"Unknown tool: {tool_name}")

    args = call.get("args", {})
    if not isinstance(args, dict):
        return Err("Tool 'args' must be JSON object")

    try:
        # Global context injection - all tools get access to agent context
        if hasattr(config, "sandbox"):
            args["sandbox"] = config.sandbox
        if user_id:
            args["user_id"] = user_id

        result = await tool.execute(**args)

        if result.success:
            tool_result = result.unwrap()
            # Convert ToolResult to string for agent consumption
            return Ok(tool_result.for_agent())
        return Err(f"Tool {tool_name} failed: {result.error}")

    except Exception as e:
        return Err(f"Tool {tool_name} execution failed: {str(e)}")
