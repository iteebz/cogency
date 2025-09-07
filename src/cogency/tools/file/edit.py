"""File editing tool."""

from pathlib import Path

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from ..security import resolve_path_safely
from .utils import categorize_file, format_size


class FileEdit(Tool):
    """Edit specific lines in files."""

    @property
    def name(self) -> str:
        return "edit"

    @property
    def description(self) -> str:
        return "Replace text in file"

    @property
    def schema(self) -> dict:
        return {"file": {}, "old": {}, "new": {}}

    async def execute(
        self, file: str, old: str, new: str, sandbox: bool = True
    ) -> Result[ToolResult]:
        if not file:
            return Err("File cannot be empty")

        if not old:
            return Err("Old text cannot be empty")

        try:
            if sandbox:
                # Sandboxed execution
                sandbox_dir = Path(".sandbox")
                file_path = resolve_path_safely(file, sandbox_dir)
            else:
                # Direct filesystem access with traversal protection
                file_path = resolve_path_safely(file)

            # Read existing content
            if not file_path.exists():
                return Err(f"File '{file}' does not exist")

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Count matches for intelligent feedback
            matches = content.count(old)

            if matches == 0:
                return Err(f"Text not found: '{old}'\n* Check exact spelling, whitespace, and case")

            if matches > 1:
                return self._handle_multiple_matches(content, old, matches)

            # Single match - perform replacement
            new_content = content.replace(old, new, 1)

            # Write back
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            outcome = f"File edited: {file} (1 replacement)"
            return Ok(ToolResult(outcome))

        except ValueError as e:
            return Err(f"Security violation: {str(e)}")
        except Exception as e:
            return Err(f"Failed to edit '{file}': {str(e)}")

    def _format_edit_result(
        self, filename: str, old_text: str, new_text: str, file_path: Path
    ) -> str:
        """Format edit result with file context."""
        stat = file_path.stat()
        size = format_size(stat.st_size)
        category = categorize_file(file_path)

        header = f"Replaced text in '{filename}' ({size}) [{category}]"

        if category == "code":
            ext = file_path.suffix.lower()
            if ext in [".py", ".js", ".ts", ".go", ".rs"]:
                header += f" {ext[1:].upper()}"

        # Show the actual change - truncate if too long
        old_display = old_text[:50] + "..." if len(old_text) > 50 else old_text
        new_display = new_text[:50] + "..." if len(new_text) > 50 else new_text
        diff = f"- {old_display}\n+ {new_display}"

        return f"{header}\n{diff}"

    def _handle_multiple_matches(self, content: str, old: str, matches: int) -> Result[str]:
        """Handle multiple matches with context for agent guidance."""
        lines = content.split("\n")
        match_contexts = []

        # Find line numbers where matches occur
        for i, line in enumerate(lines, 1):
            if old in line:
                # Show context around the match
                start_ctx = max(0, i - 2)
                end_ctx = min(len(lines), i + 1)
                context_lines = lines[start_ctx:end_ctx]

                # Highlight the matching line
                context = []
                for j, ctx_line in enumerate(context_lines):
                    line_num = start_ctx + j + 1
                    prefix = ">" if line_num == i else " "
                    context.append(f"{prefix} {line_num:3d}: {ctx_line}")

                match_contexts.append("\n".join(context))

                if len(match_contexts) >= 5:  # Limit to first 5 matches
                    break

        error_msg = f"Found {matches} matches for '{old}'. Be more specific:\n\n"
        error_msg += "\n\n".join([f"Match {i + 1}:\n{ctx}" for i, ctx in enumerate(match_contexts)])
        error_msg += "\n\n* Include more surrounding context to make the match unique"

        return Err(error_msg)
