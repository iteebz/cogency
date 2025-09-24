"""Tool execution helpers with cohesive execution context."""

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
        return ToolResult(outcome=f"{tool_name} not found: Tool '{tool_name}' not registered")

    args = dict(call.args)
    if tool_name == "shell":
        args["timeout"] = execution.shell_timeout
    if tool_name == "web_scrape":
        args["scrape_limit"] = execution.scrape_limit
    if user_id:
        args["user_id"] = user_id

    return await tool.execute(**args)


__all__ = ["execute_tool"]
