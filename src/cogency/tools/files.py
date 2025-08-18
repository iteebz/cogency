"""Files: File operations for sandbox environment."""

from pathlib import Path

from ..lib.result import Err, Ok, Result
from .base import Tool


class FileRead(Tool):
    """Read content from a file."""

    @property
    def name(self) -> str:
        return "file_read"

    @property
    def description(self) -> str:
        return "Read content from a file. Args: filename (str)"

    async def execute(self, filename: str) -> Result[str, str]:
        try:
            file_path = Path(".sandbox") / filename
            with open(file_path) as f:
                content = f.read()

            line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            result = f"Read '{filename}' ({len(content)} chars, {line_count} lines)\n\n{content}"
            return Ok(result)

        except FileNotFoundError:
            return Err(f"File not found: {filename}")
        except Exception as e:
            return Err(f"Failed to read '{filename}': {str(e)}")


class FileWrite(Tool):
    """Write content to a file."""

    @property
    def name(self) -> str:
        return "file_write"

    @property
    def description(self) -> str:
        return "Write content to a file. Args: filename (str), content (str)"

    async def execute(self, filename: str, content: str) -> Result[str, str]:
        try:
            # Ensure sandbox directory exists
            sandbox = Path(".sandbox")
            sandbox.mkdir(exist_ok=True)

            file_path = sandbox / filename
            with open(file_path, "w") as f:
                f.write(content)

            line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
            result = f"Wrote '{filename}' ({len(content)} chars, {line_count} lines)"
            return Ok(result)

        except Exception as e:
            return Err(f"Failed to write '{filename}': {str(e)}")


class FileList(Tool):
    """List files in sandbox directory."""

    @property
    def name(self) -> str:
        return "file_list"

    @property
    def description(self) -> str:
        return "List files in sandbox directory. No args needed"

    async def execute(self) -> Result[str, str]:
        try:
            sandbox = Path(".sandbox")
            if not sandbox.exists():
                return Ok("Sandbox directory is empty")

            files = []
            for file_path in sandbox.iterdir():
                if file_path.is_file():
                    size = file_path.stat().st_size
                    files.append(f"{file_path.name} ({size} bytes)")
                elif file_path.is_dir():
                    files.append(f"{file_path.name}/")

            if not files:
                return Ok("Sandbox directory is empty")

            result = "Sandbox contents:\n" + "\n".join(sorted(files))
            return Ok(result)
        except Exception as e:
            return Err(f"Error listing files: {str(e)}")
