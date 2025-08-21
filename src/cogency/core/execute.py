"""Tool execution - canonical JSON-based implementation."""

import json
import logging

from ..context import working
from ..lib.result import Err, Ok, Result


async def execute_tools(
    task_id: str, tools_json: str, tools: dict, user_id: str = None
) -> Result[None, str]:
    """Execute JSON tool array sequentially and update working memory."""
    logger = logging.getLogger("cogency.execute")

    if not task_id:
        return Err("task_id required")

    if not tools_json or tools_json.strip() == "[]":
        return Ok(None)

    logger.debug(f"Executing tools: {len(tools_json)} chars JSON")

    try:
        tool_calls = json.loads(tools_json)
    except json.JSONDecodeError as e:
        logger.error(f"JSON parse failed: {str(e)} - content: {tools_json[:100]}...")
        return Err(f"Invalid JSON: {str(e)}")

    if not isinstance(tool_calls, list):
        return Err("Tools must be JSON array")

    for tool_call in tool_calls:
        logger.debug(f"Executing tool: {tool_call.get('name')}")

        result = await _execute(task_id, tool_call, tools, user_id)
        if result.failure:
            logger.error(f"Tool {tool_call.get('name')} failed: {result.error}")
            return result  # Propagate failure

        logger.debug(f"Tool {tool_call.get('name')} succeeded")

    return Ok(None)


async def _execute(
    task_id: str, tool_call: dict, tools: dict, user_id: str = None
) -> Result[None, str]:
    """Execute single JSON tool call."""
    if not isinstance(tool_call, dict):
        return Err("Tool call must be JSON object")

    tool_name = tool_call.get("name")
    if not tool_name:
        return Err("Tool call missing 'name' field")

    if tool_name not in tools:
        return Err(f"Unknown tool: {tool_name}")

    args = tool_call.get("args", {})
    if not isinstance(args, dict):
        return Err("Tool 'args' must be JSON object")

    # Execute with context
    try:
        # Pass user_id as kwarg only for tools that need it (like recall)
        kwargs = dict(args)
        if user_id and tool_name == "recall":
            kwargs["user_id"] = user_id
        result = await tools[tool_name].execute(**kwargs)

        # Record action taken in working memory
        if result.success:
            working.actions(task_id, {"tool": tool_name, "args": args, "result": result.unwrap()})
            return Ok(None)  # Tool succeeded
        working.actions(task_id, {"tool": tool_name, "args": args, "error": result.error})
        return Err(f"Tool {tool_name} failed: {result.error}")  # Propagate failure

    except Exception as e:
        working.actions(task_id, {"tool": tool_name, "args": args, "error": str(e)})
        return Err(f"Tool {tool_name} execution failed: {str(e)}")
