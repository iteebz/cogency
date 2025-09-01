"""File listing tool."""

from pathlib import Path

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from .utils import categorize_file, format_size


class FileList(Tool):
    """File listing tool."""

    @property
    def name(self) -> str:
        return "list"

    @property
    def description(self) -> str:
        return "List files"

    @property
    def schema(self) -> dict:
        return {"path": {"optional": True}, "pattern": {"optional": True}}

    async def execute(self, path: str = ".", pattern: str = "*", **kwargs) -> Result[ToolResult]:
        """List files with clean tree structure and metadata."""
        try:
            # Determine target directory
            if path == ".":
                target = Path(".sandbox")
            else:
                target = Path(".sandbox") / path

            if not target.exists():
                return Err(f"Directory '{path}' does not exist")

            # Build clean tree structure
            tree = self._build_tree(target, pattern, depth=2)
            if not tree:
                return Err("No files found")

            # Format as clean tree
            content = self._format_tree(tree)

            # Format outcome
            file_count = self._count_files(tree)
            outcome = f"Directory listed ({file_count} items)"
            return Ok(ToolResult(outcome, content))

        except Exception as e:
            return Err(f"Error listing files: {str(e)}")

    def _build_tree(self, path: Path, pattern: str, depth: int, current_depth: int = 0) -> dict:
        """Build clean tree structure - directories and files with essential metadata."""
        tree = {"dirs": {}, "files": []}

        if current_depth >= depth:
            return tree

        try:
            for item in sorted(path.iterdir()):
                # Skip hidden files
                if item.name.startswith("."):
                    continue

                if item.is_dir():
                    subtree = self._build_tree(item, pattern, depth, current_depth + 1)
                    if subtree["dirs"] or subtree["files"]:  # Only include non-empty dirs
                        tree["dirs"][item.name] = subtree

                elif item.is_file():
                    # Apply pattern matching
                    if self._matches_pattern(item.name, pattern):
                        stat = item.stat()
                        tree["files"].append(
                            {
                                "name": item.name,
                                "size": stat.st_size,
                                "category": categorize_file(item),
                            }
                        )

        except PermissionError:
            pass  # Skip inaccessible directories

        return tree

    def _matches_pattern(self, filename: str, pattern: str) -> bool:
        """Simple pattern matching (supports * wildcards)."""
        if pattern == "*":
            return True

        # Convert shell-style wildcards to simple matching
        if "*" in pattern:
            parts = pattern.split("*")
            if len(parts) == 2:
                prefix, suffix = parts
                return filename.startswith(prefix) and filename.endswith(suffix)

        return pattern.lower() in filename.lower()

    def _format_tree(self, tree: dict, indent: str = "") -> str:
        """Format clean tree structure."""
        lines = []

        # Directories first
        for dir_name, subtree in tree["dirs"].items():
            lines.append(f"{indent}{dir_name}/")
            # Recursive formatting with increased indent
            lines.append(self._format_tree(subtree, indent + "  "))

        for file_info in tree["files"]:
            name = file_info["name"]
            size = format_size(file_info["size"])
            category = file_info["category"]
            lines.append(f"{indent}{name} [{category}] {size}")

        return "\n".join(line for line in lines if line.strip())

    def _count_files(self, tree: dict) -> int:
        """Count total files recursively."""
        count = len(tree["files"])
        for subtree in tree["dirs"].values():
            count += self._count_files(subtree)
        return count
