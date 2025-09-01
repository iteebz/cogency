"""File reading tool."""

from pathlib import Path

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from ..security import safe_path
from .utils import categorize_file, format_size


class FileRead(Tool):
    """File reading with intelligent context and formatting."""

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return "Read file content"

    @property
    def schema(self) -> dict:
        return {
            "file": {},
            "start": {"type": "integer", "optional": True},
            "lines": {"type": "integer", "optional": True},
        }

    async def execute(
        self, file: str, start: int = 0, lines: int = 100, sandbox: bool = True, **kwargs
    ) -> Result[ToolResult]:
        if not file:
            return Err("File cannot be empty")

        try:
            if sandbox:
                # Sandboxed execution
                sandbox_dir = Path(".sandbox")
                file_path = safe_path(sandbox_dir, file)
            else:
                # Direct filesystem access
                file_path = Path(file).resolve()

            # Read specific lines if requested - PERFORMANCE WIN
            if start > 0 or lines != 100:
                content = self._read_lines(file_path, start, lines)
                end_line = start + (lines - 1) if lines else "end"
                outcome = f"File read from {file} (lines {start}-{end_line})"
            else:
                # Read entire file - default behavior
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                outcome = f"File read from {file}"

            return Ok(ToolResult(outcome, content))

        except FileNotFoundError:
            location = "sandbox" if sandbox else "filesystem"
            return Err(
                f"File not found: {file} (searched in {location})\n* Use 'list' to see available files"
            )
        except UnicodeDecodeError:
            return Err(f"File '{file}' contains binary data - cannot display as text")
        except ValueError as e:
            return Err(f"Security violation: {str(e)}")
        except Exception as e:
            return Err(f"Failed to read '{file}': {str(e)}")

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

    def _format_content(self, filename: str, content: str, file_path: Path) -> str:
        """Format file content with intelligent context."""
        if not content:
            return f"📄 {filename} (empty file)"

        stat = file_path.stat()
        size = format_size(stat.st_size)
        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        # Categorize file
        category = categorize_file(file_path)

        header = f"📄 {filename} ({size}, {line_count} lines) [{category}]"

        if category == "code":
            ext = file_path.suffix.lower()
            if ext in [".py", ".js", ".ts", ".go", ".rs"]:
                header += f" {ext[1:].upper()}"

        if len(content) > 5000:
            preview = content[:5000]
            return f"{header}\n\n{preview}\n\n[File truncated at 5,000 characters. Full size: {len(content):,} chars]\n* File is large - consider using 'shell' with 'head' or 'tail' for specific sections"

        return f"{header}\n\n{content}"
