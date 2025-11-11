from .codec import format_results_array
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
    """Execute multiple tool calls sequentially, maintaining order.

    Args:
        calls: List of tool calls to execute in order
        execution: Execution context with tools and configuration
        user_id: User identifier for tool execution context
        conversation_id: Conversation identifier for tool execution context

    Returns:
        List of ToolResult in same order as input calls.
        Failures don't block subsequent calls - all execute regardless.
    """
    results = []
    for call in calls:
        result = await execute_tool(
            call,
            execution=execution,
            user_id=user_id,
            conversation_id=conversation_id,
        )
        results.append(result)
    return results


def format_results_for_injection(calls: list[ToolCall], results: list[ToolResult]) -> str:
    """Format results as XML-wrapped JSON array for LLM injection.

    Wraps the results array in <results> tags per XML protocol spec.
    Ready for injection into next turn's LLM context.

    Args:
        calls: List of ToolCall objects (for tool names, in order)
        results: List of ToolResult in same order as calls

    Returns:
        String: "<results>[...json array...]</results>"
    """
    array_json = format_results_array(calls, results)
    return f"<results>\n{array_json}\n</results>"


__all__ = ["execute_tools", "format_results_for_injection"]
