"""File reading tool - handles errors internally."""

from pathlib import Path

from ...core.protocols import Tool, ToolResult
from ..security import get_safe_file_path, safe_execute


class FileRead(Tool):
    """File reading with intelligent context and formatting."""

    name = "read"
    description = "Read file content"
    schema = {
        "file": {},
        "start": {"type": "integer", "optional": True},
        "lines": {"type": "integer", "optional": True},
    }

    @safe_execute
    async def execute(
        self, file: str, start: int = 0, lines: int = 100, sandbox: bool = True, **kwargs
    ) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty")

        try:
            file_path = get_safe_file_path(file, sandbox)

            # Read content based on parameters
            if start > 0 or lines != 100:
                content = self._read_lines(file_path, start, lines)
                line_count = content.count("\n") + 1 if content else 0
                outcome = f"Read {file} lines {start}-{start + lines - 1} ({line_count} lines)"
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                line_count = content.count("\n") + 1 if content else 0
                outcome = f"Read {file} ({line_count} lines)"

            return ToolResult(outcome=outcome, content=content)

        except UnicodeDecodeError:
            return ToolResult(
                outcome=f"File '{file}' contains binary data - cannot display as text"
            )

    def _read_lines(self, file_path: Path, start: int, lines: int = None) -> str:
        """Read specific lines from file - performance optimized."""
        result_lines = []
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 0):  # Zero-indexed
                if line_num < start:
                    continue
                if lines and len(result_lines) >= lines:
                    break
                result_lines.append(line.rstrip("\n"))

        return "\n".join(result_lines)
