from pathlib import Path

from ..core.config import Access
from ..core.protocols import Tool, ToolResult
from ..core.security import resolve_file, safe_execute


class Read(Tool):
    """Read file."""

    name = "read"
    description = "Read file. start/lines for pagination."
    schema = {
        "file": {},
        "start": {"type": "integer", "optional": True},
        "lines": {"type": "integer", "optional": True},
    }

    def describe(self, args: dict) -> str:
        file = args.get("file", "file")
        start = args.get("start")
        lines = args.get("lines")

        if start is not None or lines is not None:
            parts = []
            if start is not None:
                parts.append(f"from line {start}")
            if lines is not None:
                parts.append(f"{lines} lines")
            return f"Reading {file} ({', '.join(parts)})"

        return f"Reading {file}"

    @safe_execute
    async def execute(
        self,
        file: str,
        start: int = 0,
        lines: int | None = None,
        sandbox_dir: str = ".cogency/sandbox",
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty", error=True)

        file_path = resolve_file(file, access, sandbox_dir)

        try:
            if not file_path.exists():
                return ToolResult(
                    outcome=f"File '{file}' not found. Try: list to browse, find to search by name.",
                    error=True,
                )

            if file_path.is_dir():
                return ToolResult(
                    outcome=f"'{file}' is a directory. Try: list to explore it.",
                    error=True,
                )

            if start > 0 or lines is not None:
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
        """Read specific lines from file with line numbers."""
        result_lines = []
        with open(file_path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 0):
                if line_num < start:
                    continue
                if lines and len(result_lines) >= lines:
                    break
                result_lines.append(f"{line_num}: {line.rstrip(chr(10))}")

        return "\n".join(result_lines)
