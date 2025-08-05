"""Core action functions - consolidated business logic."""

from typing import Any, Dict, List, Tuple

from resilient_result import Result

from cogency.tools.base import Tool


async def execute_single_tool(
    tool_name: str, tool_args: dict, tools: List[Tool]
) -> Tuple[str, Dict, Any]:
    """Execute a tool with built-in capability restrictions."""

    async def _execute() -> Tuple[str, Dict, Any]:
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


def format_tool_input(tool_instance, tool_name: str, tool_args: dict) -> str:
    """Format tool input for display."""
    if tool_instance:
        arg_str, _ = tool_instance.format_human(tool_args)
        return arg_str
    else:
        if tool_args:
            first_key = next(iter(tool_args))
            first_val = str(tool_args[first_key])
            return f"({first_val})"
        return ""


def format_tool_result(tool_instance, tool_name: str, tool_args: dict, tool_output) -> str:
    """Format tool result for display."""
    if tool_instance:
        _, result_str = tool_instance.format_human(tool_args, tool_output)
        return result_str
    else:
        # Fallback formatting
        if isinstance(tool_output.data, dict) and "summary" in tool_output.data:
            return tool_output.data.get("summary", "")
        else:
            result = str(tool_output.data)
            return result[:100] + ("..." if len(result) > 100 else "")


def prepare_completed_results(successes: List[dict], failures: List[dict]) -> List[dict]:
    """Prepare results for state completion."""
    return successes + failures


def generate_execution_summary(successes: List[dict], failures: List[dict]) -> str:
    """Generate summary of tool execution."""
    summary_parts = []
    if successes:
        summary_parts.append(f"{len(successes)} tools executed successfully")
    if failures:
        summary_parts.append(f"{len(failures)} tools failed")

    return "; ".join(summary_parts) if summary_parts else "No tools executed"
