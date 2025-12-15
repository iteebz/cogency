import asyncio

from .config import Execution
from .protocols import ToolCall, ToolResult


async def execute_tool(
    call: ToolCall,
    *,
    execution: Execution,
    user_id: str,
    conversation_id: str,
) -> ToolResult:
    tool_name = call.name

    tool = next((t for t in execution.tools if t.name == tool_name), None)
    if not tool:
        return ToolResult(outcome=f"Tool '{tool_name}' not registered", error=True)

    args = dict(call.args)

    args["storage"] = execution.storage
    args["sandbox_dir"] = execution.sandbox_dir
    args["access"] = execution.access

    if tool_name == "shell":
        args["timeout"] = execution.shell_timeout
    if user_id:
        args["user_id"] = user_id

    try:
        return await tool.execute(**args)
    except Exception as e:
        return ToolResult(outcome=f"Tool execution failed: {str(e)}", error=True)


async def execute_tools(
    calls: list[ToolCall],
    *,
    execution: Execution,
    user_id: str,
    conversation_id: str,
) -> list[ToolResult]:
    """Execute multiple tool calls in parallel, preserving result order.

    Args:
        calls: List of tool calls to execute
        execution: Execution context with tools and configuration
        user_id: User identifier for tool execution context
        conversation_id: Conversation identifier for tool execution context

    Returns:
        List of ToolResult in same order as input calls.
        Failures don't block other calls - all execute regardless.
    """
    if not calls:
        return []

    tasks = [
        execute_tool(
            call,
            execution=execution,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        for call in calls
    ]
    return list(await asyncio.gather(*tasks))


__all__ = ["execute_tools"]
