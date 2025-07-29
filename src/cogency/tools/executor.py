"""Tool execution utilities."""

from typing import Any, Dict, List, Tuple

from resilient_result import Result

from cogency.tools import Tool
from cogency.utils import format_tool_error


async def execute_single_tool(
    tool_name: str, tool_args: dict, tools: List[Tool]
) -> Tuple[str, Dict, Any]:
    """Execute a tool with structured error handling."""

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


async def execute_tools(
    tool_calls: List[Tuple[str, Dict]], tools: List[Tool], state, notify=None
) -> Dict[str, Any]:
    """Execute tools with error isolation."""
    if not tool_calls:
        print("execute_tools: No tool calls, returning empty result.")
        return Result.ok(
            {
                "results": [],
                "errors": [],
                "summary": "No tools to execute",
            }
        )

    successes = []
    failures = []

    # Get tool emojis for progress display
    tool_emoji_map = {tool.name: getattr(tool, "emoji", "⚡") for tool in tools}

    for tool_name, tool_args in tool_calls:
        # Find the tool instance for formatting
        tool_instance = next((t for t in tools if t.name == tool_name), None)

        # Show tool execution start if state is available
        if state:
            tool_emoji = tool_emoji_map.get(tool_name, "💡")

            # Use tool's format method for params, otherwise fallback
            if tool_instance:
                param_str, _ = tool_instance.format_human(tool_args)
                tool_input = param_str
            else:
                tool_input = ""
                if tool_args:
                    first_key = next(iter(tool_args))
                    first_val = str(tool_args[first_key])[:60] + (
                        "..." if len(str(tool_args[first_key])) > 60 else ""
                    )
                    tool_input = f"({first_val})"

            if notify:
                notify("action", f"{tool_emoji} {tool_name}{tool_input}")

        try:
            result = await execute_single_tool(tool_name, tool_args, tools)
            actual_tool_name, actual_args, tool_output = result

            if not tool_output.success:
                # Use user-friendly error message
                raw_error = tool_output.error or "Unknown error"
                user_friendly_error = format_tool_error(actual_tool_name, Exception(raw_error))
                if notify:
                    notify("action", f"✗ {user_friendly_error}\n")
                failure_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "error": user_friendly_error,
                    "error_type": "tool_execution_error",
                }
                failures.append(failure_result)
            else:
                tool_result = tool_output.data

                # Show result using tool's format method if available
                if state:
                    if tool_instance:
                        _, result_str = tool_instance.format_human(actual_args, tool_output)
                        readable_result = result_str
                    else:
                        # Fallback formatting
                        if isinstance(tool_result, dict) and "summary" in tool_result:
                            readable_result = tool_result.get("summary", "")
                        else:
                            readable_result = str(tool_result)[:100] + (
                                "..." if len(str(tool_result)) > 100 else ""
                            )

                    # Add success indicator to result
                    if notify:
                        notify("action", f"✓ {readable_result}\n")

                success_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "result": tool_result,
                }
                successes.append(success_result)

        except Exception as e:
            # Use user-friendly error message
            user_friendly_error = format_tool_error(tool_name, e)
            if notify:
                notify("action", f"✗ {user_friendly_error}")
            failure_result = {
                "tool_name": tool_name,
                "args": tool_args,
                "error": user_friendly_error,
                "error_type": "execution_error",
            }
            failures.append(failure_result)

    # Generate summary
    summary_parts = []
    if successes:
        summary_parts.append(f"{len(successes)} tools executed successfully")
    if failures:
        summary_parts.append(f"{len(failures)} tools failed")

    summary = "; ".join(summary_parts) if summary_parts else "No tools executed"

    final_result = Result.ok(
        {
            "results": successes,
            "errors": failures,
            "summary": summary,
            "total_executed": len(tool_calls),
            "successful_count": len(successes),
            "failed_count": len(failures),
        }
    )
    print(f"execute_tools: Returning final_result: {final_result}")
    return final_result


async def run_tools(tool_calls: List[Tuple[str, Dict]], tools: List[Tool], state, notify=None) -> Dict[str, Any]:
    """Execute tools."""
    return await execute_tools(tool_calls, tools, state, notify)
