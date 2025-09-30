from pathlib import Path

from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class FileRead(Tool):
    """Read file content."""

    name = "file_read"
    description = "Read file content"
    schema = {
        "file": {},
        "start": {"type": "integer", "optional": True},
        "lines": {"type": "integer", "optional": True},
    }

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        return f"Reading {args.get('file', 'file')}"

    @safe_execute
    async def execute(
        self,
        file: str,
        start: int = 0,
        lines: int = 100,
        base_dir: str | None = None,
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty")

        file_path = resolve_file(file, access, base_dir)

        try:
            if not file_path.exists():
                return ToolResult(outcome=f"File '{file}' does not exist")

            if start > 0 or lines != 100:
                content = self._read_lines(file_path, start, lines)
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

            return ToolResult(outcome=f"Read {file}", content=content)

        except UnicodeDecodeError:
            return ToolResult(outcome=f"File '{file}' contains binary data")

    def _read_lines(self, file_path: Path, start: int, lines: int = None) -> str:
        """Read specific lines from file."""
        result_lines = []
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 0):
                if line_num < start:
                    continue
                if lines and len(result_lines) >= lines:
                    break
                result_lines.append(line.rstrip("\n"))

        return "\n".join(result_lines)
