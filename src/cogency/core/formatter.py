"""Reference-grade formatting for tool calls and results.

Cathedral principle: All formatting logic centralized in one place.
Clean abstractions for any consumer (display, resume, websocket, api).
"""

from .protocols import ToolCall, ToolResult

# Tool call display formats - centralized and extensible
CALL_FORMATS = {
    "write": lambda args: f"Creating {args.get('file', 'file')}",
    "read": lambda args: f"Reading {args.get('file', 'file')}",
    "shell": lambda args: f"Running {args.get('command', 'command')}",
    "search": lambda args: f'Searching "{args.get("query", "query")}"',
    "recall": lambda args: f'Recalling "{args.get("query", "query")}"',
    "scrape": lambda args: f"Scraping {args.get('url', 'url')}",
    "list": lambda args: f"Listing {args.get('path', '.')}",
    "edit": lambda args: f"Editing {args.get('file', 'file')}",
}


class Formatter:
    """Reference-grade formatter for tool interactions.

    Provides clean abstractions for formatting tool calls and results
    for different consumers (humans, agents, APIs, etc).
    """

    @staticmethod
    def tool_call_human(call: ToolCall) -> str:
        """Format tool call for human display - semantic action."""
        formatter = CALL_FORMATS.get(call.name, lambda args: f"Running {call.name}")
        return formatter(call.args)

    @staticmethod
    def tool_call_agent(call: ToolCall) -> str:
        """Format tool call for agent consumption - full JSON context."""
        return call.to_json()

    @staticmethod
    def tool_result_human(result: ToolResult) -> str:
        """Format tool result for human display - clean outcome."""
        return result.outcome

    @staticmethod
    def tool_result_agent(result: ToolResult) -> str:
        """Format tool result for agent consumption - outcome + full content."""
        if result.content:
            return f"{result.outcome}\n\n{result.content}"
        return result.outcome
