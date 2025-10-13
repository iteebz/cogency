import difflib

from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class Edit(Tool):
    """Edit file."""

    name = "edit"
    description = "Edit file by replacing text. Match must be unique."
    schema = {"file": {}, "old": {}, "new": {}}

    def describe(self, args: dict) -> str:
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

        if not old:  # Catches "" and None
            return ToolResult(
                outcome="Text to replace cannot be empty. Use 'write' to create or overwrite files.",
                error=True,
            )

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
                outcome=f"Found {matches} matches for '{old}' - be more specific",
                error=True,
            )

        new_content = content.replace(old, new, 1)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        diff = self._compute_diff(file, content, new_content)

        actual_added = 0
        actual_removed = 0
        for line in diff.splitlines():
            if line.startswith("+") and not line.startswith("+++"):
                actual_added += 1
            elif line.startswith("-") and not line.startswith("---"):
                actual_removed += 1

        return ToolResult(
            outcome=f"Edited {file} (+{actual_added}/-{actual_removed})", content=diff
        )

    def _compute_diff(self, file: str, old: str, new: str) -> str:
        old_lines = old.splitlines(keepends=True)
        new_lines = new.splitlines(keepends=True)
        diff = difflib.unified_diff(old_lines, new_lines, fromfile=file, tofile=file, lineterm="")
        return "".join(diff)
