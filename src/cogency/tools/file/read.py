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
        sandbox_dir: str = ".cogency/sandbox",
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty", error=True)

        file_path = resolve_file(file, access, sandbox_dir)

        try:
            if not file_path.exists():
                return ToolResult(outcome=f"File '{file}' does not exist", error=True)

            if start > 0 or lines != 100:
                content = self._read_lines(file_path, start, lines)
                line_count = len(content.splitlines())
                outcome = f"Read {file} ({line_count} lines)"
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                line_count = len(content.splitlines())
                outcome = f"Read {file} ({line_count} lines)"

            return ToolResult(outcome=outcome, content=content)

        except UnicodeDecodeError:
            return ToolResult(outcome=f"File '{file}' contains binary data", error=True)

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
