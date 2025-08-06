"""Tool execution utilities."""

from typing import Any, Dict, List, Tuple

from resilient_result import Result

from cogency.events import emit
from cogency.tools.base import Tool

from .core import (
    execute_single_tool,
)


async def execute_tools(
    tool_calls: List[Tuple[str, Dict]],
    tools: List[Tool],
    state,
) -> Dict[str, Any]:
    """Execute tools with error isolation."""
    if not tool_calls:
        return Result.ok(
            {
                "results": [],
                "errors": [],
                "summary": "No tools to execute",
            }
        )

    successes = []
    failures = []

    for tool_name, tool_args in tool_calls:
        # Find the tool instance for formatting
        tool_instance = next((t for t in tools if t.name == tool_name), None)

        # Show tool execution start if state is available
        if state:
            tool_input, _ = tool_instance.format_human(tool_args) if tool_instance else ("", "")
            emit("action", state="executing", tool=tool_name, input=tool_input)

        try:
            result = await execute_single_tool(tool_name, tool_args, tools)
            actual_tool_name, actual_args, tool_output = result

            if not tool_output.success:
                # Use user-friendly error message
                raw_error = tool_output.error or "Unknown error"
                user_friendly_error = f"{actual_tool_name} failed: {raw_error}"
                emit(
                    "tool",
                    name=actual_tool_name,
                    ok=False,
                    error=user_friendly_error,
                    args=actual_args,
                )
                failure_result = {
                    "name": actual_tool_name,
                    "args": actual_args,
                    "success": False,
                    "result": tool_output,  # Keep Result object
                    "error": str(tool_output.error)
                    if hasattr(tool_output, "error")
                    else "Unknown error",
                }
                failures.append(failure_result)
            else:
                # tool_result = tool_output.data # No longer needed here

                # Show result using tool's format method if available
                if state:
                    _, readable_result = (
                        tool_instance.format_human(actual_args, tool_output)
                        if tool_instance
                        else ("", str(tool_output.data))
                    )
                    emit(
                        "tool",
                        name=actual_tool_name,
                        ok=True,
                        result=readable_result,
                        args=actual_args,
                    )

                success_result = {
                    "name": actual_tool_name,
                    "args": actual_args,
                    "success": True,
                    "result": tool_output,  # Keep Result object
                    "error": None,
                }
                successes.append(success_result)
                if state:
                    state.execution.tool_results[actual_tool_name] = tool_output.data

        except Exception as e:
            # Use user-friendly error message
            user_friendly_error = f"{tool_name} failed: {str(e)}"
            emit("tool", name=tool_name, ok=False, error=user_friendly_error)
            failure_result = {
                "name": tool_name,
                "args": tool_args,
                "success": False,
                "result": Result.fail(str(e)),  # Keep Result object
                "error": str(e),
            }
            failures.append(failure_result)

    # Generate summary
    # Generate execution summary
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
    return final_result
