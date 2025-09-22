"""File editing with exact string replacement and duplicate detection."""

from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class FileEdit(Tool):
    """Replace text in files."""

    name = "file_edit"
    description = "Replace text in file"
    schema = {"file": {}, "old": {}, "new": {}}

    def __init__(self, access: Access = "sandbox"):
        self.access = access

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        return f"Editing {args.get('file', 'file')}"

    @safe_execute
    async def execute(self, file: str, old: str, new: str, **kwargs) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty")

        if not old:
            return ToolResult(outcome="Old text cannot be empty")

        file_path = resolve_file(file, self.access)

        if not file_path.exists():
            return ToolResult(outcome=f"File '{file}' does not exist")

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        if old not in content:
            return ToolResult(outcome=f"Text not found: '{old}'")

        matches = content.count(old)
        if matches > 1:
            return ToolResult(outcome=f"Found {matches} matches for '{old}' - be more specific")

        new_content = content.replace(old, new, 1)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        return ToolResult(outcome=f"File edited: {file}")
