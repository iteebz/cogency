"""File writing with sandbox/system mode support."""

from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class FileWrite(Tool):
    """Write content to file."""

    name = "file_write"
    description = "Write content to file"
    schema = {"file": {}, "content": {}}

    def __init__(self, access: Access = "sandbox"):
        self.access = access

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        return f"Creating {args.get('file', 'file')}"

    @safe_execute
    async def execute(self, file: str, content: str, **kwargs) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty")

        file_path = resolve_file(file, self.access)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return ToolResult(outcome=f"Created {file}")
