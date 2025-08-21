"""File reading with intelligent context and formatting."""

from pathlib import Path

from ...core.protocols import Tool
from ...lib.result import Err, Ok, Result
from ..security import safe_path
from .utils import categorize_file, format_size


class FileRead(Tool):
    """Enhanced file reading with intelligent context and formatting."""

    @property
    def name(self) -> str:
        return "read"

    @property
    def description(self) -> str:
        return "Read file content with intelligent formatting. Args: filename (str)"

    @property
    def schema(self) -> dict:
        return {
            "filename": {"type": "str", "required": True, "description": "Path to file to read"}
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {"task": "Read config file", "call": {"filename": "config.json"}},
            {"task": "Read source code", "call": {"filename": "main.py"}},
            {"task": "Read documentation", "call": {"filename": "README.md"}},
        ]

    async def execute(self, filename: str) -> Result[str, str]:
        if not filename:
            return Err("Filename cannot be empty")

        try:
            sandbox_dir = Path(".sandbox")
            file_path = safe_path(sandbox_dir, filename)

            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Enhanced formatting with context
            formatted = self._format_content(filename, content, file_path)
            return Ok(formatted)

        except FileNotFoundError:
            return Err(f"File not found: {filename}\n💡 Use 'list' to see available files")
        except UnicodeDecodeError:
            return Err(f"File '{filename}' contains binary data - cannot display as text")
        except ValueError as e:
            return Err(f"Security violation: {str(e)}")
        except Exception as e:
            return Err(f"Failed to read '{filename}': {str(e)}")

    def _format_content(self, filename: str, content: str, file_path: Path) -> str:
        """Format file content with intelligent context."""
        if not content:
            return f"📄 {filename} (empty file)"

        # Get file stats
        stat = file_path.stat()
        size = format_size(stat.st_size)
        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        # Categorize file
        category = categorize_file(file_path)

        # Build header with context
        header = f"📄 {filename} ({size}, {line_count} lines) [{category}]"

        # Add syntax context for code files
        if category == "code":
            ext = file_path.suffix.lower()
            if ext in [".py", ".js", ".ts", ".go", ".rs"]:
                header += f" {ext[1:].upper()}"

        # Handle large files intelligently
        if len(content) > 5000:
            preview = content[:5000]
            return f"{header}\n\n{preview}\n\n[File truncated at 5,000 characters. Full size: {len(content):,} chars]\n💡 File is large - consider using 'shell' with 'head' or 'tail' for specific sections"

        return f"{header}\n\n{content}"
