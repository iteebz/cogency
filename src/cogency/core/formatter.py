"""Reference-grade formatting for tool calls and results.

Cathedral principle: All formatting logic centralized in one place.
Clean abstractions for any consumer (display, resume, websocket, api).
"""

from .protocols import ToolCall, ToolResult

# Tool call display formats - centralized and extensible
CALL_FORMATS = {
    "file_write": lambda args: f"Creating {args.get('file', 'file')}",
    "file_read": lambda args: f"Reading {args.get('file', 'file')}",
    "file_edit": lambda args: f"Editing {args.get('file', 'file')}",
    "file_list": lambda args: f"Listing {args.get('path', '.')}",
    "file_search": lambda args: f'Searching files for "{args.get("query", "query")}"',
    "web_search": lambda args: f'Web searching "{args.get("query", "query")}"',
    "web_scrape": lambda args: f"Scraping {args.get('url', 'url')}",
    "recall": lambda args: f'Recalling "{args.get("query", "query")}"',
    "shell": lambda args: f"Running {args.get('command', 'command')}",
}


class Formatter:
    """Reference-grade formatter for tool interactions.

    Provides clean abstractions for formatting tool calls and results
    for different consumers (humans, agents, APIs, etc).
    """

    @staticmethod
    def tool_call_human(call: ToolCall) -> str:
        """Format tool call for human display - semantic action."""
        # Look up tool instance by name
        from ..tools import TOOLS
        tool_instance = next((t for t in TOOLS if t.name == call.name), None)
        
        if tool_instance and hasattr(tool_instance, 'describe'):
            return tool_instance.describe(call.args)
        
        # Fallback to format dict (for tools not yet updated)
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
