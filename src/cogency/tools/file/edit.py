from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class FileEdit(Tool):
    """Replace text in files."""

    name = "file_edit"
    description = "Replace text in file"
    schema = {"file": {}, "old": {}, "new": {}}

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        return f"Editing {args.get('file', 'file')}"

    @safe_execute
    async def execute(
        self,
        file: str,
        old: str,
        new: str,
        sandbox_dir: str = ".cogency/sandbox",
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty", error=True)

        if not old:
            return ToolResult(outcome="Old text cannot be empty", error=True)

        file_path = resolve_file(file, access, sandbox_dir)

        if not file_path.exists():
            return ToolResult(outcome=f"File '{file}' does not exist", error=True)

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        if old not in content:
            return ToolResult(outcome=f"Text not found: '{old}'", error=True)

        matches = content.count(old)
        if matches > 1:
            return ToolResult(
                outcome=f"Found {matches} matches for '{old}' - be more specific", error=True
            )

        new_content = content.replace(old, new, 1)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        added = new.count("\n") + 1
        removed = old.count("\n") + 1
        return ToolResult(outcome=f"Modified {file} (+{added}/-{removed})")
