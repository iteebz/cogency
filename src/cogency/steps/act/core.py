"""Core action functions - consolidated business logic."""

from typing import Any

from resilient_result import Result

from cogency.tools.base import Tool


async def execute_single_tool(
    tool_name: str, tool_args: dict, tools: list[Tool]
) -> tuple[str, dict, Any]:
    """Execute a tool with built-in capability restrictions."""

    async def _execute() -> tuple[str, dict, Any]:
        for tool in tools:
            if tool.name == tool_name:
                try:
                    result = await tool.execute(**tool_args)
                    return tool_name, tool_args, result
                except Exception as e:
                    return (
                        tool_name,
                        tool_args,
                        Result.fail(f"Tool execution failed: {str(e)}"),
                    )
        raise ValueError(f"Tool '{tool_name}' not found.")

    return await _execute()
