"""File writing with intelligent feedback and context awareness."""

from pathlib import Path

from ...core.protocols import Tool
from ...lib.result import Err, Ok, Result
from ..security import safe_path, validate_input
from .utils import categorize_file, format_size


class FileWrite(Tool):
    """Enhanced file writing with intelligent feedback and context awareness."""

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return (
            "Write content to file with intelligent feedback. Args: filename (str), content (str)"
        )

    @property
    def schema(self) -> dict:
        return {
            "filename": {"type": "str", "required": True, "description": "Path to file to write"},
            "content": {"type": "str", "required": True, "description": "Content to write to file"},
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {
                "task": "Create Python script",
                "call": {"filename": "hello.py", "content": "print('Hello, world!')"},
            },
            {
                "task": "Save configuration",
                "call": {"filename": "config.json", "content": '{"debug": true}'},
            },
            {
                "task": "Write documentation",
                "call": {
                    "filename": "README.md",
                    "content": "# Project Title\n\nDescription here.",
                },
            },
        ]

    async def execute(self, filename: str, content: str) -> Result[str, str]:
        if not filename:
            return Err("Filename cannot be empty")

        if not validate_input(content):
            return Err("Content contains unsafe patterns")

        try:
            # Ensure sandbox directory exists
            sandbox_dir = Path(".sandbox")
            sandbox_dir.mkdir(exist_ok=True)

            file_path = safe_path(sandbox_dir, filename)

            # Check if overwriting existing file
            is_overwrite = file_path.exists()
            old_size = file_path.stat().st_size if is_overwrite else 0

            # Write with UTF-8 encoding
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            # Enhanced feedback with context
            result = self._format_write_result(filename, content, file_path, is_overwrite, old_size)
            return Ok(result)

        except ValueError as e:
            return Err(f"Security violation: {str(e)}")
        except Exception as e:
            return Err(f"Failed to write '{filename}': {str(e)}")

    def _format_write_result(
        self, filename: str, content: str, file_path: Path, is_overwrite: bool, old_size: int
    ) -> str:
        """Format write result with intelligent context."""
        # Basic metrics
        size = format_size(len(content.encode("utf-8")))
        line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)

        # Categorize file
        category = categorize_file(file_path)

        # Build result message
        action = "Updated" if is_overwrite else "Created"
        header = f"✓ {action} '{filename}' ({size}, {line_count} lines) [{category}]"

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

        # Add helpful context
        context = self._get_write_context(filename, content, category)
        if context:
            header += f"\n💡 {context}"

        return header

    def _get_write_context(self, filename: str, content: str, category: str) -> str:
        """Provide intelligent context for written files."""
        # Python files
        if category == "code" and filename.endswith(".py"):
            if "def " in content or "class " in content:
                return "Python code detected. Use 'shell python filename.py' to execute."
            return "Python script ready. Use 'shell python filename.py' to run."

        # JavaScript/Node files
        if category == "code" and filename.endswith((".js", ".ts")):
            if "function " in content or "const " in content:
                return "JavaScript code detected. Use 'shell node filename.js' to execute."

        # Configuration files
        elif category == "config":
            return "Configuration file saved. Changes may require restart of related services."

        # Data files
        elif category == "data":
            if filename.endswith(".csv"):
                return "CSV data saved. Use 'read filename.csv' to verify or 'shell head filename.csv' for preview."
            if filename.endswith(".json"):
                return "JSON data saved. Use 'read filename.json' to verify structure."

        # Large files
        elif len(content) > 10000:
            return "Large file created. Use 'shell head filename' or 'shell tail filename' for previews."

        # Documentation
        elif category == "docs":
            return "Documentation saved. Use 'read filename' to review content."

        return None
