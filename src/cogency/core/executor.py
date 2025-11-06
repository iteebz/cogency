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

    return await tool.execute(**args)


__all__ = ["execute_tool"]
