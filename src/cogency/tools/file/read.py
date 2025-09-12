"""File reading tool."""

from pathlib import Path

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from ..security import resolve_path_safely


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

    def describe_action(self, file: str, **kwargs) -> str:
        return f"Reading {file}"

    async def execute(
        self, file: str, start: int = 0, lines: int = 100, sandbox: bool = True, **kwargs
    ) -> Result[ToolResult]:
        if not file:
            return Err("File cannot be empty")

        try:
            if sandbox:
                # Sandboxed execution
                from ...lib.storage import Paths

                sandbox_dir = Paths.sandbox()
                file_path = resolve_path_safely(file, sandbox_dir)
            else:
                # Direct filesystem access with traversal protection
                file_path = resolve_path_safely(file)

            # Read content based on parameters
            if start > 0 or lines != 100:
                content = self._read_lines(file_path, start, lines)
                line_count = content.count('\n') + 1 if content else 0
                outcome = f"Read {file} lines {start}-{start + lines - 1} ({line_count} lines)"
            else:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()
                line_count = content.count('\n') + 1 if content else 0
                outcome = f"Read {file} ({line_count} lines)"

            return Ok(ToolResult(outcome=outcome, content=content))

        except FileNotFoundError:
            location = "sandbox" if sandbox else "filesystem"
            return Err(f"File not found: {file} (searched in {location})")
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
