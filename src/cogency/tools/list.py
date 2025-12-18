import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

from cogency.core.config import Access
from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import resolve_file, safe_execute
from cogency.core.tool import tool

# Default directory traversal depth for tree listings. Based on:
# - Depth 2: Too shallow, misses nested src/lib/components structure
# - Depth 3: Covers typical project layouts (src/module/submodule)
# - Depth 4+: Excessive output, usually includes generated/vendor dirs
# Trade-off: Readability vs completeness for typical project navigation
DEFAULT_TREE_DEPTH = 3
DEFAULT_IGNORED_DIRS = [
    "node_modules",
    ".venv",
    "__pycache__",
    "dist",
    ".git",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    ".vscode",
    ".idea",
]


@dataclass
class ListParams:
    path: Annotated[
        str, ToolParam(description="Directory path to list (relative to project root)")
    ] = "."
    pattern: Annotated[
        str | None, ToolParam(description="Filter filenames by pattern (e.g., '*.py')")
    ] = None


def _build_tree(
    path: Path,
    pattern: str,
    depth: int,
    *,
    stats: dict[str, int],
    current_depth: int = 0,
    prefix: str = "",
) -> list[str]:
    lines: list[str] = []

    if current_depth >= depth:
        return lines

    try:
        items = sorted(path.iterdir(), key=lambda x: (x.is_file(), x.name))

        for item in items:
            if item.name.startswith(".") or item.name in DEFAULT_IGNORED_DIRS:
                continue

            if item.is_dir():
                stats["dirs"] += 1
                lines.append(f"{prefix}{item.name}/")
                sub_lines = _build_tree(
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


@tool("List files in tree view (depth 3). Pattern filters filenames.")
@safe_execute
async def List(
    params: ListParams,
    sandbox_dir: str = ".cogency/sandbox",
    access: Access = "sandbox",
    **kwargs: Any,
) -> ToolResult:
    pattern = params.pattern if params.pattern is not None else "*"

    if params.path == ".":
        if access == "sandbox":
            target = Path(sandbox_dir)
            target.mkdir(parents=True, exist_ok=True)
        else:
            target = Path.cwd()
    else:
        target = resolve_file(params.path, access, sandbox_dir)

    if not target.exists():
        return ToolResult(outcome=f"Directory '{params.path}' does not exist", error=True)

    stats = {"files": 0, "dirs": 0}

    tree_lines = _build_tree(target, pattern, depth=DEFAULT_TREE_DEPTH, stats=stats)

    if not tree_lines:
        return ToolResult(outcome="Listed 0 items", content="No files found")

    content = "\n".join(tree_lines)
    total_items = stats["files"] + stats["dirs"]
    if stats["dirs"] and stats["files"]:
        outcome = f"Listed {total_items} items ({stats['dirs']} dirs, {stats['files']} files)"
    elif stats["dirs"]:
        outcome = f"Listed {stats['dirs']} {'dir' if stats['dirs'] == 1 else 'dirs'}"
    else:
        outcome = f"Listed {stats['files']} {'file' if stats['files'] == 1 else 'files'}"

    return ToolResult(outcome=outcome, content=f"Contents:\n{content}")
