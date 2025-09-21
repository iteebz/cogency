"""Formatting for tool calls and results with human/agent variants."""

from ..core.protocols import Tool, ToolCall, ToolResult


def tool_instructions(tools: list[Tool]) -> str:
    """Generate dynamic tool instructions for LLM context."""
    lines = []

    for tool in tools:
        params = []
        if hasattr(tool, "schema") and tool.schema:
            for param, info in tool.schema.items():
                if info.get("required", True):
                    params.append(param)
                else:
                    params.append(f"{param}?")
            param_str = ", ".join(params)
            lines.append(f"{tool.name}({param_str}) - {tool.description}")

    return "TOOLBOX:\n" + "\n".join(lines)


def format_call_human(call: ToolCall) -> str:
    """Format tool call for human display - semantic action."""
    from . import tools

    tool_instance = tools.get(call.name)
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
