"""File writing tool."""

from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class FileWrite(Tool):
    """Write content to file."""

    name = "file_write"
    description = "Write content to file"
    schema = {"file": {}, "content": {}}

    @safe_execute
    async def execute(self, file: str, content: str, sandbox: bool = True, **kwargs) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty")

        file_path = resolve_file(file, sandbox)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return ToolResult(outcome=f"Created {file}")
