"""File listing tool with clean tree output."""

from pathlib import Path

from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class FileList(Tool):
    """List files and directories in clean tree format."""

    name = "file_list"
    description = "List files and directories"
    schema = {"path": {"optional": True}, "pattern": {"optional": True}}

    def __init__(self, access: Access = "sandbox"):
        self.access = access

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        return f"Listing {args.get('path', '.')}"

    @safe_execute
    async def execute(self, path: str = ".", pattern: str = None, **kwargs) -> ToolResult:
        """List files in clean tree format."""
        if pattern is None:
            pattern = "*"

        # Determine target directory
        if path == ".":
            from ...lib.paths import Paths

            target = (
                Paths.sandbox()
                if self.access == "sandbox"
                else (Path.cwd() if self.access == "project" else Path("."))
            )
        else:
            target = resolve_file(path, self.access)

        if not target.exists():
            return ToolResult(outcome=f"Directory '{path}' does not exist")

        # Build tree structure
        tree_lines = self._build_tree(target, pattern, depth=2)

        if not tree_lines:
            return ToolResult(outcome="No files found")

        content = "\n".join(tree_lines)
        outcome = f"Listed {len([line for line in tree_lines if not line.endswith('/')])} items"

        return ToolResult(outcome=outcome, content=content)

    def _build_tree(
        self, path: Path, pattern: str, depth: int, current_depth: int = 0, prefix: str = ""
    ) -> list:
        """Build clean tree lines."""
        lines = []

        if current_depth >= depth:
            return lines

        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

            for item in items:
                if item.name.startswith("."):
                    continue

                if item.is_dir():
                    lines.append(f"{prefix}{item.name}/")
                    sub_lines = self._build_tree(
                        item, pattern, depth, current_depth + 1, prefix + "  "
                    )
                    lines.extend(sub_lines)

                elif item.is_file() and self._matches_pattern(item.name, pattern):
                    lines.append(f"{prefix}{item.name}")

        except PermissionError:
            pass

        return lines

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching."""
        if pattern == "*":
            return True

        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return filename.startswith(prefix) and filename.endswith(suffix)

        return pattern.lower() in filename.lower()
