"""File writing tool."""

from pathlib import Path

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from ..security import safe_path, validate_input
from .utils import categorize_file, format_size


class FileWrite(Tool):
    """File writing with intelligent feedback and context awareness."""

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return "Write content to file"

    @property
    def schema(self) -> dict:
        return {"filename": {}, "content": {}}

    async def execute(
        self, filename: str, content: str, sandbox: bool = True, **kwargs
    ) -> Result[ToolResult]:
        if not filename:
            return Err("Filename cannot be empty")

        if not validate_input(content):
            return Err("Content contains unsafe patterns")

        try:
            if sandbox:
                # Sandboxed execution
                sandbox_dir = Path(".sandbox")
                sandbox_dir.mkdir(exist_ok=True)
                file_path = safe_path(sandbox_dir, filename)
            else:
                # Direct filesystem access
                file_path = Path(filename).resolve()

            # Check if overwriting existing file
            is_overwrite = file_path.exists()
            file_path.stat().st_size if is_overwrite else 0

            # Write with UTF-8 encoding
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Clear completion signal
            outcome = f"File written to {filename}"
            return Ok(ToolResult(outcome))

        except ValueError as e:
            return Err(f"Security violation: {str(e)}")
        except Exception as e:
            return Err(f"Failed to write '{filename}': {str(e)}")

    def _feedback(
        self, filename: str, content: str, file_path: Path, is_overwrite: bool, old_size: int
    ) -> str:
        # Basic metrics
        size = format_size(len(content.encode("utf-8")))
        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        # Categorize file
        category = categorize_file(file_path)

        # Build result message
        action = "Updated" if is_overwrite else "Created"
        header = f"{action} '{filename}' ({size}, {line_count} lines) [{category}]"

        # Add syntax context for code files
        if category == "code":
            ext = file_path.suffix.lower()
            if ext in [".py", ".js", ".ts", ".go", ".rs"]:
                header += f" {ext[1:].upper()}"

        # Add change context for overwrites
        if is_overwrite:
            old_size_formatted = format_size(old_size)
            if old_size != len(content.encode("utf-8")):
                change = "larger" if len(content.encode("utf-8")) > old_size else "smaller"
                header += f"\nSize change: {old_size_formatted} → {size} ({change})"

        return header
