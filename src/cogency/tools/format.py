"""Formatting for tool calls and results with human/agent variants."""

from ..core.protocols import ToolCall, ToolResult


def format_call_human(call: ToolCall) -> str:
    """Format tool call for human display - semantic action."""
    from ..tools import TOOLS

    tool_instance = next((t for t in TOOLS if t.name == call.name), None)
    if not tool_instance:
        return f"Tool {call.name} not available"

    return tool_instance.describe(call.args)


def format_call_agent(call: ToolCall) -> str:
    """Format tool call for agent consumption - full JSON context."""
    return call.to_json()


def format_result_human(result: ToolResult) -> str:
    """Format tool result for human display - clean outcome."""
    return result.outcome


def format_result_agent(result: ToolResult) -> str:
    """Format tool result for agent consumption - outcome + full content."""
    if result.content:
        return f"{result.outcome}\n\n{result.content}"
    return result.outcome
