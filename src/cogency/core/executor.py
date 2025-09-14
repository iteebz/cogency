"""Single tool execution - pure tool running logic.

ZEALOT ARCHITECTURE: Execute ONE tool call at a time.
Multi-tool calls were premature optimization.
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
    # Note: Persistence handled by accumulator for ACID properties
    return tool_result
