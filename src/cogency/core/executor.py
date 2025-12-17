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
    args["conversation_id"] = conversation_id

    if tool_name == "shell":
        args["timeout"] = execution.shell_timeout
    if user_id:
        args["user_id"] = user_id

    try:
        return await tool.execute(**args)
    except Exception as e:
        return ToolResult(outcome=f"Tool execution failed: {e!s}", error=True)


async def execute_tools(
    calls: list[ToolCall],
    *,
    execution: Execution,
    user_id: str,
    conversation_id: str,
) -> list[ToolResult]:
    """Parallel execution, order preserved. Failures don't block siblings."""
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
