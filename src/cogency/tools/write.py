from dataclasses import dataclass
from typing import Annotated, Any

from cogency.core.config import Access
from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import resolve_file, safe_execute
from cogency.core.tool import tool


@dataclass
class WriteParams:
    file: Annotated[str, ToolParam(description="File path to write (relative to project root)")]
    content: Annotated[str, ToolParam(description="File content to write")]
    overwrite: Annotated[bool, ToolParam(description="Overwrite file if exists")] = False


@tool("Write file. Fails if file exists unless overwrite=true.")
@safe_execute
async def Write(
    params: WriteParams,
    sandbox_dir: str = ".cogency/sandbox",
    access: Access = "sandbox",
    **kwargs: Any,
) -> ToolResult:
    if not params.file:
        return ToolResult(outcome="File cannot be empty", error=True)

    file_path = resolve_file(params.file, access, sandbox_dir)

    if file_path.exists() and not params.overwrite:
        return ToolResult(
            outcome=f"File '{params.file}' already exists. Try: overwrite=True to replace, or choose different name.",
            error=True,
        )

    file_path.parent.mkdir(parents=True, exist_ok=True)

    with file_path.open("w", encoding="utf-8") as f:
        f.write(params.content)

    lines = params.content.count("\n") + 1 if params.content else 0
    preview = params.content[:200] + ("..." if len(params.content) > 200 else "")
    return ToolResult(outcome=f"Wrote {params.file} (+{lines}/-0)", content=preview)
