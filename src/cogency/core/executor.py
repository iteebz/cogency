"""Single tool execution - pure tool running logic.

ZEALOT ARCHITECTURE: Execute ONE tool call at a time.
Multi-tool calls were premature optimization bullshit.
Natural reasoning: think → act → think → act.
"""

import json
import time

from ..lib.logger import logger
from ..lib.storage import save_message
from .protocols import ToolResult


async def execute(call: dict, config, user_id: str, conversation_id: str) -> ToolResult:
    """Execute single tool call."""
    timestamp = time.time()

    # Validation errors
    if not isinstance(call, dict):
        return ToolResult(outcome="invalid call format")

    tool_name = call.get("name")
    if not tool_name:
        return ToolResult(outcome="missing tool name")

    # Find tool in config
    tool = next((t for t in config.tools if t.name == tool_name), None)
    if not tool:
        return ToolResult(outcome=f"{tool_name} not found: Tool '{tool_name}' not registered")

    args = call.get("args", {})
    if not isinstance(args, dict):
        return ToolResult(outcome=f"{tool_name} invalid args")

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
            await _save_tool_execution(conversation_id, user_id, call, tool_result, timestamp)

            return tool_result  # Simple ToolResult object
        return ToolResult(outcome=f"{tool_name} failed: {result.error}")

    except Exception as e:
        return ToolResult(outcome=f"{tool_name} crashed: {str(e)}")


async def execute_calls(
    calls: list[dict], config, user_id: str, conversation_id: str
) -> list[ToolResult]:
    """Execute multiple tool calls."""
    return [await execute(call, config, user_id, conversation_id) for call in calls]


async def _save_tool_execution(
    conversation_id: str, user_id: str, call: dict, result: ToolResult, timestamp: float
):
    execution_data = {
        "call": call,
        "result": {"outcome": result.outcome, "content": result.content},
        "timestamp": timestamp,
    }

    save_success = await save_message(
        conversation_id, user_id, "tool", json.dumps(execution_data), timestamp=timestamp
    )
    if not save_success:
        logger.warning(f"Failed to persist tool execution for conversation {conversation_id}")
