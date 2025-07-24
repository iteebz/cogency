"""Tool execution utilities."""

from typing import Any, Dict, List, Tuple

from cogency.tools.base import BaseTool
from cogency.utils.results import ToolResult


async def execute_single_tool(
    tool_name: str, tool_args: dict, tools: List[BaseTool], context=None
) -> Tuple[str, Dict, Any]:
    """Execute a tool with structured error handling."""

    async def _execute() -> Tuple[str, Dict, Any]:
        for tool in tools:
            if tool.name == tool_name:
                try:
                    # Inject context for user isolation if tool supports it
                    if context:
                        # Check if tool accepts _context parameter
                        import inspect

                        sig = inspect.signature(tool.run)
                        if "_context" in sig.parameters:
                            tool_args["_context"] = context
                        elif any(
                            p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
                        ):
                            # Only inject if it has **kwargs AND the operation method can handle it
                            # For now, don't inject into tools with dispatch patterns until we have better detection
                            pass
                    result = await tool.execute(**tool_args)
                    return tool_name, tool_args, result
                except Exception as e:
                    return (
                        tool_name,
                        tool_args,
                        ToolResult.fail(f"Tool execution failed: {str(e)}"),
                    )
        raise ValueError(f"Tool '{tool_name}' not found.")

    return await _execute()


async def execute_tools(
    tool_calls: List[Tuple[str, Dict]], tools: List[BaseTool], context, output=None
) -> Dict[str, Any]:
    """Execute tools with error isolation."""
    if not tool_calls:
        return ToolResult(
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

        # Show tool execution start if output is available
        if output:
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

            await output.update(f"{tool_emoji} {tool_name}{tool_input}")

        try:
            result = await execute_single_tool(tool_name, tool_args, tools, context)
            actual_tool_name, actual_args, tool_output = result

            if not tool_output.success:
                error_msg = tool_output.error or "Unknown error"
                if output:
                    await output.update(f"✗ {error_msg}")
                failure_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "error": error_msg,
                    "error_type": "tool_execution_error",
                }
                failures.append(failure_result)
            else:
                tool_result = tool_output.data

                # Show result using tool's format method if available
                if output:
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

                    await output.update(f"✓ {readable_result}")

                success_result = {
                    "tool_name": actual_tool_name,
                    "args": actual_args,
                    "result": tool_result,
                }
                successes.append(success_result)
                context.add_result(actual_tool_name, actual_args, tool_result)

        except Exception as e:
            error_msg = str(e)
            if output:
                await output.update(f"✗ {error_msg}")
            failure_result = {
                "tool_name": tool_name,
                "args": tool_args,
                "error": error_msg,
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

    # Add execution log to context
    combined_output = "Tool execution results:\n"
    for success in successes:
        combined_output += f"✓ {success['tool_name']}: {success['result']}\n"
    for failure in failures:
        combined_output += f"✗ {failure['tool_name']}: {failure['error']}\n"

    # Tool results stored in state, not conversation messages

    return ToolResult(
        {
            "results": successes,
            "errors": failures,
            "summary": summary,
            "total_executed": len(tool_calls),
            "successful_count": len(successes),
            "failed_count": len(failures),
        }
    )


async def run_tools(
    tool_calls: List[Tuple[str, Dict]], tools: List[BaseTool], context, output=None
) -> Dict[str, Any]:
    """Execute tools."""
    return await execute_tools(tool_calls, tools, context, output)
