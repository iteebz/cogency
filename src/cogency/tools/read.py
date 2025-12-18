from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

from cogency.core.config import Access
from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import resolve_file, safe_execute
from cogency.core.tool import tool


@dataclass
class ReadParams:
    file: Annotated[str, ToolParam(description="File path to read (relative to project root)")]
    start: Annotated[int, ToolParam(description="Starting line number (0-indexed)", ge=0)] = 0
    lines: Annotated[
        int | None, ToolParam(description="Number of lines to read", ge=1, le=10000)
    ] = None


def _read_lines(file_path: Path, start: int, lines: int | None = None) -> str:
    result_lines: list[str] = []
    with file_path.open(encoding="utf-8") as f:
        for line_num, line in enumerate(f, 0):
            if line_num < start:
                continue
            if lines and len(result_lines) >= lines:
                break
            result_lines.append(f"{line_num}: {line.rstrip(chr(10))}")

    return "\n".join(result_lines)


@tool("Read file. Use start/lines for pagination on large files.")
@safe_execute
async def Read(
    params: ReadParams,
    sandbox_dir: str = ".cogency/sandbox",
    access: Access = "sandbox",
    **kwargs: Any,
) -> ToolResult:
    if not params.file:
        return ToolResult(outcome="File cannot be empty", error=True)

    file_path = resolve_file(params.file, access, sandbox_dir)

    try:
        if not file_path.exists():
            return ToolResult(
                outcome=f"File '{params.file}' not found. Try: list to browse, find to search by name.",
                error=True,
            )

        if file_path.is_dir():
            return ToolResult(
                outcome=f"'{params.file}' is a directory. Try: list to explore it.",
                error=True,
            )

        if params.start > 0 or params.lines is not None:
            content = _read_lines(file_path, params.start, params.lines)
            line_count = len(content.splitlines())
            outcome = f"Read {params.file} ({line_count} lines)"
        else:
            with file_path.open(encoding="utf-8") as f:
                content = f.read()
            line_count = len(content.splitlines())
            outcome = f"Read {params.file} ({line_count} lines)"

        return ToolResult(outcome=outcome, content=content)

    except UnicodeDecodeError:
        return ToolResult(outcome=f"File '{params.file}' contains binary data", error=True)
