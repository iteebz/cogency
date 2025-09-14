"""Single tool execution - pure tool running logic.

ZEALOT ARCHITECTURE: Execute ONE tool call at a time.
Multi-tool calls were premature optimization bullshit.
Natural reasoning: think → act → think → act.
"""

import json
import time

from ..lib.logger import logger
from ..lib.storage import save_message
from .protocols import ToolCall, ToolResult


async def execute(call: ToolCall, config, user_id: str, conversation_id: str) -> ToolResult:
    timestamp = time.time()

    tool_name = call.name

    tool = next((t for t in config.tools if t.name == tool_name), None)
    if not tool:
        return ToolResult(outcome=f"{tool_name} not found: Tool '{tool_name}' not registered")

    args = call.args
    if hasattr(config, "sandbox"):
        args["sandbox"] = config.sandbox
    if user_id:
        args["user_id"] = user_id

    tool_result = await tool.execute(**args)
    await _save_tool_execution(conversation_id, user_id, call, tool_result, timestamp)

    return tool_result


async def execute_calls(
    calls: list[ToolCall], config, user_id: str, conversation_id: str
) -> list[ToolResult]:
    return [await execute(call, config, user_id, conversation_id) for call in calls]


async def _save_tool_execution(
    conversation_id: str, user_id: str, call: ToolCall, result: ToolResult, timestamp: float
):
    execution_data = {
        "call": {"name": call.name, "args": call.args},
        "result": {"outcome": result.outcome, "content": result.content},
        "timestamp": timestamp,
    }

    save_success = await save_message(
        conversation_id, user_id, "tool", json.dumps(execution_data), timestamp=timestamp
    )
    if not save_success:
        logger.warning(f"Failed to persist tool execution for conversation {conversation_id}")
