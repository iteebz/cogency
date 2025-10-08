import fnmatch
from pathlib import Path

from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute

DEFAULT_TREE_DEPTH = 3


class Ls(Tool):
    """List files."""

    name = "ls"
    description = "List files."
    schema = {"path": {"optional": True}, "pattern": {"optional": True}}

    def describe(self, args: dict) -> str:
        return f"Listing {args.get('path', '.')}"

    @safe_execute
    async def execute(
        self,
        path: str = ".",
        pattern: str = None,
        sandbox_dir: str = ".cogency/sandbox",
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if pattern is None:
            pattern = "*"

        if path == ".":
            if access == "sandbox":
                target = Path(sandbox_dir)
                target.mkdir(parents=True, exist_ok=True)
            else:
                target = Path.cwd()
        else:
            target = resolve_file(path, access, sandbox_dir)

        if not target.exists():
            return ToolResult(outcome=f"Directory '{path}' does not exist", error=True)

        stats = {"files": 0, "dirs": 0}

        # Build tree structure
        tree_lines = self._build_tree(target, pattern, depth=DEFAULT_TREE_DEPTH, stats=stats)

        if not tree_lines:
            return ToolResult(outcome="Listed directory", content="No files found")

        content = "\n".join(tree_lines)
        total_items = stats["files"] + stats["dirs"]
        if stats["dirs"] and stats["files"]:
            outcome = f"Listed {total_items} items ({stats['dirs']} dirs, {stats['files']} files)"
        elif stats["dirs"]:
            outcome = f"Listed {stats['dirs']} {'dir' if stats['dirs'] == 1 else 'dirs'}"
        else:
            outcome = f"Listed {stats['files']} {'file' if stats['files'] == 1 else 'files'}"

        return ToolResult(outcome=outcome, content=content)

    def _build_tree(
        self,
        path: Path,
        pattern: str,
        depth: int,
        *,
        stats: dict[str, int],
        current_depth: int = 0,
        prefix: str = "",
    ) -> list:
        """Build tree lines."""
        lines = []

        if current_depth >= depth:
            return lines

        try:
            items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

            for item in items:
                if item.name.startswith("."):
                    continue

                if item.is_dir():
                    stats["dirs"] += 1
                    if item.name != "dist":
                        lines.append(f"{prefix}{item.name}/")
                    sub_lines = self._build_tree(
                        item,
                        pattern,
                        depth,
                        stats=stats,
                        current_depth=current_depth + 1,
                        prefix=prefix + "  ",
                    )
                    lines.extend(sub_lines)

                elif item.is_file() and fnmatch.fnmatch(item.name, pattern):
                    stats["files"] += 1
                    lines.append(f"{prefix}{item.name}")

        except PermissionError:
            pass

        return lines
