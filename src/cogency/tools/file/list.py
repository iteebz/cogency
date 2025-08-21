"""Enhanced file listing with hierarchical context and intelligence."""

from pathlib import Path

from ...core.protocols import Tool
from ...lib.result import Err, Ok, Result
from .utils import categorize_file, format_size


class FileList(Tool):
    """Enhanced file listing with hierarchical context and intelligence."""

    @property
    def name(self) -> str:
        return "list"

    @property
    def description(self) -> str:
        return "List files with hierarchical structure and intelligence. Args: depth (int, default 2), pattern (str, default '*'), details (bool, default False), show_hidden (bool, default False)"

    @property
    def schema(self) -> dict:
        return {
            "depth": {
                "type": "int",
                "required": False,
                "default": 2,
                "description": "Directory depth to traverse",
            },
            "pattern": {
                "type": "str",
                "required": False,
                "default": "*",
                "description": "File pattern to match (e.g., '*.py', '*test*')",
            },
            "details": {
                "type": "bool",
                "required": False,
                "default": False,
                "description": "Show detailed file information",
            },
            "show_hidden": {
                "type": "bool",
                "required": False,
                "default": False,
                "description": "Include hidden files and directories",
            },
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {"task": "List all files", "call": {}},
            {"task": "List Python files only", "call": {"pattern": "*.py"}},
            {"task": "Show detailed file info", "call": {"details": True}},
            {"task": "Deep directory scan", "call": {"depth": 4}},
            {"task": "Find test files", "call": {"pattern": "*test*", "depth": 3}},
        ]

    async def execute(
        self,
        depth: int = 2,
        pattern: str = "*",
        details: bool = False,
        show_hidden: bool = False,
    ) -> Result[str, str]:
        """Enhanced file listing with LS-style context intelligence."""
        try:
            sandbox = Path(".sandbox")
            if not sandbox.exists():
                return Ok("Sandbox directory is empty")

            # Build hierarchical structure
            tree = self._build_tree(sandbox, depth, pattern, show_hidden)
            if not tree:
                return Ok("No files match the specified pattern")

            # Format with beautiful tree structure
            result = self._format_tree(tree, details, sandbox)
            summary = self._get_summary(tree)

            return Ok(f"{result}\n\n{summary}")

        except Exception as e:
            return Err(f"Error listing files: {str(e)}")

    def _build_tree(
        self, path: Path, max_depth: int, pattern: str, show_hidden: bool, current_depth: int = 0
    ) -> dict:
        """Build hierarchical file structure like LS tool."""
        tree = {"dirs": {}, "files": []}

        if current_depth >= max_depth:
            return tree

        try:
            for item in sorted(path.iterdir()):
                # Skip hidden files unless requested
                if not show_hidden and item.name.startswith("."):
                    continue

                if item.is_dir():
                    subtree = self._build_tree(
                        item, max_depth, pattern, show_hidden, current_depth + 1
                    )
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
                                "modified": stat.st_mtime,
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

    def _format_tree(self, tree: dict, details: bool, base_path: Path) -> str:
        """Format as beautiful tree structure."""
        lines = [f"Sandbox Structure ({base_path.name}):"]
        self._format_tree_recursive(tree, lines, "", details)
        return "\n".join(lines)

    def _format_tree_recursive(self, tree: dict, lines: list, prefix: str, details: bool):
        """Recursively format tree structure."""
        items = []

        # Add directories first
        for dir_name, subtree in tree["dirs"].items():
            items.append(("dir", dir_name, subtree))

        # Add files second
        for file_info in tree["files"]:
            items.append(("file", file_info, None))

        for i, (item_type, item_data, subtree) in enumerate(items):
            is_last = i == len(items) - 1
            current_prefix = "└── " if is_last else "├── "
            next_prefix = prefix + ("    " if is_last else "│   ")

            if item_type == "dir":
                lines.append(f"{prefix}{current_prefix}{item_data}/")
                self._format_tree_recursive(subtree, lines, next_prefix, details)
            else:
                # File formatting
                file_info = item_data
                name = file_info["name"]
                size = format_size(file_info["size"])
                category = file_info["category"]

                if details:
                    import time

                    mod_time = time.strftime(
                        "%Y-%m-%d %H:%M", time.localtime(file_info["modified"])
                    )
                    lines.append(
                        f"{prefix}{current_prefix}{name:<20} {size:>8} {mod_time} [{category}]"
                    )
                else:
                    lines.append(f"{prefix}{current_prefix}{name} ({size}) [{category}]")

    def _get_summary(self, tree: dict) -> str:
        """Generate project summary for agent context."""
        total_files = 0
        total_dirs = 0
        total_size = 0
        categories = {}

        def count_recursive(subtree):
            nonlocal total_files, total_dirs, total_size

            total_dirs += len(subtree["dirs"])
            total_files += len(subtree["files"])

            for file_info in subtree["files"]:
                total_size += file_info["size"]
                category = file_info["category"]
                categories[category] = categories.get(category, 0) + 1

            for subdir_tree in subtree["dirs"].values():
                count_recursive(subdir_tree)

        count_recursive(tree)

        summary_parts = [
            f"Total: {total_files} files, {total_dirs} directories, {format_size(total_size)}"
        ]

        if categories:
            cat_summary = ", ".join([f"{count} {cat}" for cat, count in sorted(categories.items())])
            summary_parts.append(f"Types: {cat_summary}")

        return " | ".join(summary_parts)
