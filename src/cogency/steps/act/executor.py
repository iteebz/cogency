"""Tool execution utilities."""

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


async def execute_tools(
    tool_calls: List[Tuple[str, Dict]],
    tools: List[Tool],
    state,
    notifier=None,
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

    # Progress display handled by notifier

    for tool_name, tool_args in tool_calls:
        # Find the tool instance for formatting
        tool_instance = next((t for t in tools if t.name == tool_name), None)

        # Show tool execution start if state is available
        if state:
            # Use tool's format method for args, otherwise fallback
            if tool_instance:
                arg_str, _ = tool_instance.format_human(tool_args)
                tool_input = arg_str
            else:
                tool_input = ""
                if tool_args:
                    first_key = next(iter(tool_args))
                    first_val = str(tool_args[first_key])
                    tool_input = f"({first_val})"

            if notifier:
                await notifier("action", state="executing", tool=tool_name, input=tool_input)

        try:
            result = await execute_single_tool(tool_name, tool_args, tools)
            actual_tool_name, actual_args, tool_output = result

            # Debug prints removed - use notifier if needed

            if not tool_output.success:
                # Use user-friendly error message
                raw_error = tool_output.error or "Unknown error"
                user_friendly_error = f"{actual_tool_name} failed: {raw_error}"
                if notifier:
                    await notifier(
                        "tool", name=actual_tool_name, ok=False, error=user_friendly_error
                    )
                failure_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "result_object": tool_output,  # Store the full Result object
                }
                failures.append(failure_result)
            else:
                # tool_result = tool_output.data # No longer needed here

                # Show result using tool's format method if available
                if state:
                    if tool_instance:
                        _, result_str = tool_instance.format_human(actual_args, tool_output)
                        readable_result = result_str
                    else:
                        # Fallback formatting
                        if isinstance(tool_output.data, dict) and "summary" in tool_output.data:
                            readable_result = tool_output.data.get("summary", "")
                        else:
                            readable_result = str(tool_output.data)[:100] + (
                                "..." if len(str(tool_output.data)) > 100 else ""
                            )

                    # Add success indicator to result
                    if notifier:
                        await notifier(
                            "tool", name=actual_tool_name, ok=True, result=readable_result
                        )

                success_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "result_object": tool_output,  # Store the full Result object
                }
                successes.append(success_result)
                if state:
                    state.execution.tool_results[actual_tool_name] = tool_output.data

        except Exception as e:
            # Use user-friendly error message
            user_friendly_error = f"{tool_name} failed: {str(e)}"
            if notifier:
                await notifier("tool", name=tool_name, ok=False, error=user_friendly_error)
            failure_result = {
                "tool_name": tool_name,
                "args": tool_args,
                "result_object": Result.fail(user_friendly_error),  # Store a Result.fail object
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
    return final_result
