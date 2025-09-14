"""File editing tool."""

from ...core.protocols import Tool, ToolResult
from ..security import get_safe_file_path, safe_execute


class FileEdit(Tool):
    """Edit specific lines in files."""

    name = "edit"
    description = "Replace text in file"
    schema = {"file": {}, "old": {}, "new": {}}

    @safe_execute
    async def execute(
        self, file: str, old: str, new: str, sandbox: bool = True, **kwargs
    ) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty")

        if not old:
            return ToolResult(outcome="Old text cannot be empty")

        file_path = get_safe_file_path(file, sandbox)

        # Read existing content
        if not file_path.exists():
            return ToolResult(outcome=f"File '{file}' does not exist")

        with open(file_path, encoding="utf-8") as f:
            content = f.read()

        # Count matches for intelligent feedback
        matches = content.count(old)

        if matches == 0:
            return ToolResult(
                outcome=f"Text not found: '{old}'\\n* Check exact spelling, whitespace, and case"
            )

        if matches > 1:
            return self._handle_multiple_matches(content, old, matches)

        # Single match - perform replacement
        new_content = content.replace(old, new, 1)

        # Write back
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

        outcome = f"File edited: {file} (1 replacement)"
        return ToolResult(outcome=outcome)

    def _handle_multiple_matches(self, content: str, old: str, matches: int) -> ToolResult:
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

        return ToolResult(outcome=error_msg)
