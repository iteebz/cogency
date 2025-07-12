from pathlib import Path
from typing import Any, Dict, List

from cogency.tools.base import BaseTool
from cogency.utils.interrupt import interruptable
from cogency.utils.errors import (
    ToolError,
    ValidationError,
    create_success_response,
    handle_tool_exception,
    validate_required_params,
)


class FileManagerTool(BaseTool):
    """File management tool that operates in a safe, contained directory.

    This tool provides file system operations (create, read, list, delete)
    within a specified base directory to prevent unauthorized access.
    """

    def __init__(self, base_dir: str = "workspace"):
        """Initialize the FileManager tool.

        Args:
            base_dir: Base directory for file operations (default: "workspace")
        """
        super().__init__(
            name="file_manager",
            description=(
                "Manage files and directories - create, read, list, and delete files safely."
            ),
        )
        self.base_dir = Path(base_dir).resolve()
        # Ensure base directory exists
        self.base_dir.mkdir(exist_ok=True)

    def _safe_path(self, rel_path: str) -> Path:
        """Ensure path is within base directory to prevent directory traversal."""
        if not rel_path or rel_path.strip() == "":
            raise ValidationError("Path cannot be empty", error_code="EMPTY_PATH")

        # Normalize the path and resolve it relative to base_dir
        path = (self.base_dir / rel_path).resolve()

        # Security check: ensure path is within base_dir
        if not str(path).startswith(str(self.base_dir)):
            raise ValidationError(
                f"Unsafe path access attempted: {rel_path}",
                error_code="PATH_TRAVERSAL_ATTEMPT",
                details={"attempted_path": rel_path, "base_dir": str(self.base_dir)},
            )

        return path

    @handle_tool_exception
    @interruptable
    async def run(self, action: str, filename: str = "", content: str = "") -> Dict[str, Any]:
        """Execute file operations based on action type.

        Args:
            action: Operation to perform (create_file, read_file, list_files, delete_file)
            filename: Target file or directory path
            content: Content for file creation

        Returns:
            Dict containing operation results or error information
        """
        valid_actions = ["create_file", "read_file", "list_files", "delete_file"]

        if action not in valid_actions:
            raise ValidationError(
                f"Unknown action: {action}",
                error_code="INVALID_ACTION",
                details={"valid_actions": valid_actions, "provided_action": action},
            )

        if action == "create_file":
            return self._create_file(filename, content)
        elif action == "read_file":
            return self._read_file(filename)
        elif action == "list_files":
            return self._list_files(filename if filename else ".")
        elif action == "delete_file":
            return self._delete_file(filename)

    def _create_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create a file with content."""
        validate_required_params({"filename": filename}, ["filename"], self.name)

        path = self._safe_path(filename)

        try:
            # Create parent directories if they don't exist
            path.parent.mkdir(parents=True, exist_ok=True)
            # Write content to file
            path.write_text(content, encoding="utf-8")
        except Exception as e:
            raise ToolError(
                f"Failed to create file {filename}: {str(e)}",
                error_code="FILE_CREATE_FAILED",
                details={"filename": filename, "content_length": len(content)},
            )

        return create_success_response(
            {
                "path": str(path.relative_to(self.base_dir)),
                "size": len(content),
            },
            f"Created file: {filename}",
        )

    def _read_file(self, filename: str) -> Dict[str, Any]:
        """Read a file's content."""
        validate_required_params({"filename": filename}, ["filename"], self.name)

        path = self._safe_path(filename)

        if not path.exists():
            raise ToolError(
                f"File not found: {filename}",
                error_code="FILE_NOT_FOUND",
                details={"filename": filename},
            )

        if not path.is_file():
            raise ToolError(
                f"Path is not a file: {filename}",
                error_code="NOT_A_FILE",
                details={
                    "filename": filename,
                    "path_type": "directory" if path.is_dir() else "unknown",
                },
            )

        try:
            content = path.read_text(encoding="utf-8")
        except Exception as e:
            raise ToolError(
                f"Failed to read file {filename}: {str(e)}",
                error_code="FILE_READ_FAILED",
                details={"filename": filename},
            )

        return create_success_response(
            {
                "content": content,
                "path": str(path.relative_to(self.base_dir)),
                "size": len(content),
            },
            f"Read file: {filename}",
        )

    def _list_files(self, directory: str = ".") -> Dict[str, Any]:
        """List files and directories."""
        path = self._safe_path(directory)

        if not path.exists():
            raise ToolError(
                f"Directory not found: {directory}",
                error_code="DIRECTORY_NOT_FOUND",
                details={"directory": directory},
            )

        if not path.is_dir():
            raise ToolError(
                f"Path is not a directory: {directory}",
                error_code="NOT_A_DIRECTORY",
                details={
                    "directory": directory,
                    "path_type": "file" if path.is_file() else "unknown",
                },
            )

        try:
            items = []
            for item in sorted(path.iterdir()):
                rel_path = str(item.relative_to(self.base_dir))
                items.append(
                    {
                        "name": item.name,
                        "path": rel_path,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )
        except Exception as e:
            raise ToolError(
                f"Failed to list directory {directory}: {str(e)}",
                error_code="DIRECTORY_LIST_FAILED",
                details={"directory": directory},
            )

        return create_success_response(
            {
                "items": items,
                "directory": directory,
                "total": len(items),
            },
            f"Listed {len(items)} items in {directory}",
        )

    def _delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file."""
        validate_required_params({"filename": filename}, ["filename"], self.name)

        path = self._safe_path(filename)

        if not path.exists():
            raise ToolError(
                f"File not found: {filename}",
                error_code="FILE_NOT_FOUND",
                details={"filename": filename},
            )

        if not path.is_file():
            raise ToolError(
                f"Path is not a file: {filename}",
                error_code="NOT_A_FILE",
                details={
                    "filename": filename,
                    "path_type": "directory" if path.is_dir() else "unknown",
                },
            )

        try:
            path.unlink()
        except Exception as e:
            raise ToolError(
                f"Failed to delete file {filename}: {str(e)}",
                error_code="FILE_DELETE_FAILED",
                details={"filename": filename},
            )

        return create_success_response(
            {
                "path": str(path.relative_to(self.base_dir)),
            },
            f"Deleted file: {filename}",
        )

    def get_schema(self) -> str:
        """Return tool call schema for LLM formatting."""
        return (
            "file_manager(action='create_file|read_file|list_files|delete_file', "
            "filename='path/to/file', content='file content')"
        )

    def get_usage_examples(self) -> List[str]:
        """Return example tool calls for LLM guidance."""
        return [
            "file_manager(action='create_file', filename='notes/plan.md', "
            "content='Build agent, ship blog, rest never.')",
            "file_manager(action='read_file', filename='notes/plan.md')",
            "file_manager(action='list_files', filename='notes')",
            "file_manager(action='delete_file', filename='notes/old_file.txt')",
        ]
