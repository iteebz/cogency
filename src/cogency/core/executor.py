"""Single tool execution with context injection.

Executes one tool call at a time following natural reasoning pattern:
think → call → execute → result → think

Context injection adds sandbox and user_id to all tool calls.
"""

from .protocols import ToolCall, ToolResult


async def execute(call: ToolCall, config, user_id: str, conversation_id: str) -> ToolResult:
    tool_name = call.name

    tool = next((t for t in config.tools if t.name == tool_name), None)
    if not tool:
        return ToolResult(outcome=f"{tool_name} not found: Tool '{tool_name}' not registered")

    args = call.args
    if tool_name == "shell":
        args["timeout"] = config.security.shell_timeout
    if tool_name == "web_scrape":
        args["scrape_limit"] = config.scrape_limit
    if user_id:
        args["user_id"] = user_id

    return await tool.execute(**args)
