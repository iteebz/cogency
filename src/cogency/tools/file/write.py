"""File writing tool - handles errors internally."""

from ...core.protocols import Tool, ToolResult
from ..security import get_safe_file_path, safe_execute


class FileWrite(Tool):
    """File writing with intelligent feedback and context awareness."""

    name = "write"
    description = "Write content to file"
    schema = {"file": {}, "content": {}}

    @safe_execute
    async def execute(self, file: str, content: str, sandbox: bool = True, **kwargs) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty")

        file_path = get_safe_file_path(file, sandbox)

        # Write with UTF-8 encoding
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        line_count = content.count("\n") + 1 if content else 0
        return ToolResult(
            outcome=f"Created {file} ({line_count} lines)",
            content=f"Created: {file_path}",
        )
