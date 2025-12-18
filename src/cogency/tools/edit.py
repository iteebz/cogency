import difflib
from dataclasses import dataclass
from typing import Annotated, Any

from cogency.core.config import Access
from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import resolve_file, safe_execute
from cogency.core.tool import tool


@dataclass
class EditParams:
    file: Annotated[str, ToolParam(description="File path to edit (relative to project root)")]
    old: Annotated[
        str, ToolParam(description="Text to replace (must match exactly, including whitespace)")
    ]
    new: Annotated[str, ToolParam(description="Replacement text")]


def _compute_diff(file: str, old: str, new: str) -> str:
    old_lines = old.splitlines(keepends=True)
    new_lines = new.splitlines(keepends=True)
    diff = difflib.unified_diff(old_lines, new_lines, fromfile=file, tofile=file, lineterm="")
    return "".join(diff)


@tool("Edit file by replacing text. Exact match (old) must be unique in file.")
@safe_execute
async def Edit(
    params: EditParams,
    sandbox_dir: str = ".cogency/sandbox",
    access: Access = "sandbox",
    **kwargs: Any,
) -> ToolResult:
    if not params.file:
        return ToolResult(outcome="File cannot be empty", error=True)

    if not params.old:
        return ToolResult(
            outcome="Text to replace cannot be empty. Use 'write' to create or overwrite files.",
            error=True,
        )

    file_path = resolve_file(params.file, access, sandbox_dir)

    if not file_path.exists():
        return ToolResult(
            outcome=f"File '{params.file}' not found. Try: list to browse, find to search by name.",
            error=True,
        )

    with file_path.open(encoding="utf-8") as f:
        content = f.read()

    if params.old not in content:
        return ToolResult(
            outcome=f"Text not found in '{params.file}'. Verify exact content including whitespace.",
            error=True,
        )

    matches = content.count(params.old)
    if matches > 1:
        return ToolResult(
            outcome=f"Found {matches} matches - provide more context to make it unique",
            error=True,
        )

    new_content = content.replace(params.old, params.new, 1)

    with file_path.open("w", encoding="utf-8") as f:
        f.write(new_content)

    diff = _compute_diff(params.file, content, new_content)

    actual_added = 0
    actual_removed = 0
    for line in diff.splitlines():
        if line.startswith("+") and not line.startswith("+++"):
            actual_added += 1
        elif line.startswith("-") and not line.startswith("---"):
            actual_removed += 1

    return ToolResult(
        outcome=f"Edited {params.file} (+{actual_added}/-{actual_removed})", content=diff
    )
