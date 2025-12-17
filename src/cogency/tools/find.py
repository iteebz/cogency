import re
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from cogency.core.config import Access
from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import resolve_file, safe_execute
from cogency.core.tool import tool

MAX_RESULTS = 100
SKIP_DIRS = {
    ".venv",
    "venv",
    ".env",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    "node_modules",
    ".git",
    ".hatch",
    ".tox",
    ".nox",
    "dist",
    "build",
    ".eggs",
}


@dataclass
class FindParams:
    pattern: Annotated[
        str | None, ToolParam(description="Filename pattern to match (e.g., '*.py', 'main*')")
    ] = None
    content: Annotated[str | None, ToolParam(description="Text content to search for in files")] = (
        None
    )
    path: Annotated[str, ToolParam(description="Root search path (relative to project root)")] = "."


def _matches_pattern(filename: str, pattern: str) -> bool:
    if pattern == "*":
        return True

    if "*" in pattern:
        regex_pattern = pattern.replace("*", ".*")
        return bool(re.match(regex_pattern, filename, re.IGNORECASE))

    return pattern.lower() in filename.lower()


def _search_content(file_path: Path, search_term: str) -> list:
    matches = []

    try:
        with file_path.open(encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                if search_term.lower() in line.lower():
                    matches.append((line_num, line))
    except (UnicodeDecodeError, PermissionError):
        pass

    return matches


def _search_files(
    search_path: Path,
    workspace_root: Path,
    pattern: str | None,
    content: str | None,
) -> list:
    results = []
    root = workspace_root

    def process_file(item: Path):
        if pattern and not _matches_pattern(item.name, pattern):
            return
        try:
            relative_path = item.relative_to(root)
        except ValueError:
            return
        path_str = str(relative_path)

        if content:
            matches = _search_content(item, content)
            for line_num, line_text in matches:
                results.append(f"{path_str}:{line_num}: {line_text.strip()}")
        else:
            results.append(path_str)

    if search_path.is_file():
        process_file(search_path)
        return results

    def walk(p: Path):
        try:
            for item in p.iterdir():
                if (
                    item.name.startswith(".")
                    or item.name in SKIP_DIRS
                    or item.name.endswith(".egg-info")
                ):
                    continue

                if item.is_dir():
                    walk(item)
                elif item.is_file():
                    process_file(item)
        except PermissionError:
            pass

    walk(search_path)
    return results


@tool("Find files by name pattern or search file contents.")
@safe_execute
async def Find(
    params: FindParams,
    sandbox_dir: str = ".cogency/sandbox",
    access: Access = "sandbox",
    **kwargs,
) -> ToolResult:
    if not params.pattern and not params.content:
        return ToolResult(outcome="Must specify pattern or content to search", error=True)

    if params.pattern == "*" and not params.content:
        return ToolResult(
            outcome="Pattern too broad",
            content="Specify: content='...' OR pattern='*.py' OR path='subdir'",
            error=True,
        )

    if params.path == ".":
        if access == "sandbox":
            search_path = Path(sandbox_dir).resolve()
            search_path.mkdir(parents=True, exist_ok=True)
        else:
            search_path = Path.cwd().resolve()
    else:
        search_path = resolve_file(params.path, access, sandbox_dir).resolve()

    workspace_root = search_path if access == "sandbox" else Path.cwd().resolve()

    if not search_path.is_relative_to(workspace_root):
        return ToolResult(
            outcome="Directory outside workspace scope",
            error=True,
        )

    if not search_path.exists():
        return ToolResult(outcome=f"Directory '{params.path}' does not exist", error=True)

    results = _search_files(search_path, workspace_root, params.pattern, params.content)
    total = len(results)

    def describe_root() -> str:
        try:
            relative = search_path.relative_to(workspace_root)
            return "." if str(relative) == "." else str(relative)
        except ValueError:
            return "."

    def describe_query() -> list[str]:
        lines = [f"Root: {describe_root()}"]
        if params.pattern:
            lines.append(f"Pattern: {params.pattern}")
        if params.content:
            lines.append(f"Content: {params.content}")
        return lines

    if total == 0:
        summary = "\n".join(describe_query())
        return ToolResult(
            outcome="Found 0 matches",
            content=summary,
        )

    lines = describe_query()
    lines.append("")

    shown = results[:MAX_RESULTS]
    truncated = total > MAX_RESULTS

    content_text = "\n".join(lines + shown)
    if truncated:
        content_text += f"\n\n[Truncated: showing {MAX_RESULTS} of {total}. Refine query.]"

    return ToolResult(
        outcome=f"Found {total} {'match' if total == 1 else 'matches'}",
        content=content_text,
    )
