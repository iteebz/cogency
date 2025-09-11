"""Single tool execution - pure tool running logic.

ZEALOT ARCHITECTURE: Execute ONE tool call at a time.
Multi-tool calls were premature optimization bullshit.
Natural reasoning: think → act → think → act.
"""

import json
import time

from ..lib.resilience import resilient_save
from .protocols import Event, ToolResult
from .result import Err, Ok, Result


async def execute(
    call: dict, config, user_id: str, conversation_id: str
) -> ToolResult:
    """Execute single tool call and return simple ToolResult.
    
    Returns ToolResult: Simple outcome + content for Streamer
    """
    timestamp = time.time()
    
    # Validation errors
    if not isinstance(call, dict):
        return ToolResult(outcome="invalid call format: Call must be JSON object")
    
    tool_name = call.get("name")
    if not tool_name:
        return ToolResult(outcome="missing tool name: Call missing 'name' field")

    # Find tool in config
    tool = next((t for t in config.tools if t.name == tool_name), None)
    if not tool:
        return ToolResult(outcome=f"{tool_name} not found: Tool '{tool_name}' not registered")

    args = call.get("args", {})
    if not isinstance(args, dict):
        return ToolResult(outcome=f"{tool_name} invalid args: Args must be JSON object")

    try:
        # Global context injection
        if hasattr(config, "sandbox"):
            args["sandbox"] = config.sandbox
        if user_id:
            args["user_id"] = user_id

        # Execute tool
        result = await tool.execute(**args)

        if result.success:
            tool_result = result.unwrap()
            
            # Store successful execution
            _save_tool_execution(conversation_id, user_id, call, tool_result, timestamp)
            
            return tool_result  # Simple ToolResult object
        else:
            return ToolResult(outcome=f"{tool_name} failed: {result.error}")

    except Exception as e:
        return ToolResult(outcome=f"{tool_name} crashed: {str(e)}")


async def execute_calls(
    calls: list[dict], config, user_id: str, conversation_id: str
) -> list[ToolResult]:
    """Execute multiple tool calls and return list of ToolResults.
    
    Interface for Streamer - executes each call individually.
    """
    results = []
    for call in calls:
        result = await execute(call, config, user_id, conversation_id)
        results.append(result)
    return results


def _save_tool_execution(conversation_id: str, user_id: str, call: dict, result: ToolResult, timestamp: float):
    """Save successful tool execution to DB."""
    execution_data = {
        "call": call,
        "result": {
            "outcome": result.outcome,
            "content": result.content
        },
        "timestamp": timestamp
    }
    
    resilient_save(
        conversation_id,
        user_id, 
        Event.TOOL,
        json.dumps(execution_data),
        timestamp
    )
