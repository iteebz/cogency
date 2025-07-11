from pathlib import Path
from typing import Any, Dict, List

from cogency.tools.base import BaseTool


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
            description="Manage files and directories - create, read, list, and delete files safely.",
        )
        self.base_dir = Path(base_dir).resolve()
        # Ensure base directory exists
        self.base_dir.mkdir(exist_ok=True)

    def _safe_path(self, rel_path: str) -> Path:
        """Ensure path is within base directory to prevent directory traversal."""
        if not rel_path or rel_path.strip() == "":
            raise ValueError("Path cannot be empty")

        # Normalize the path and resolve it relative to base_dir
        path = (self.base_dir / rel_path).resolve()

        # Security check: ensure path is within base_dir
        if not str(path).startswith(str(self.base_dir)):
            raise ValueError(f"Unsafe path access attempted: {rel_path}")

        return path

    def run(self, action: str, filename: str = "", content: str = "") -> Dict[str, Any]:
        """Execute file operations based on action type.

        Args:
            action: Operation to perform (create_file, read_file, list_files, delete_file)
            filename: Target file or directory path
            content: Content for file creation

        Returns:
            Dict containing operation results or error information
        """
        try:
            if action == "create_file":
                return self._create_file(filename, content)
            elif action == "read_file":
                return self._read_file(filename)
            elif action == "list_files":
                return self._list_files(filename if filename else ".")
            elif action == "delete_file":
                return self._delete_file(filename)
            else:
                return {
                    "error": f"Unknown action: {action}. Available: create_file, read_file, list_files, delete_file"
                }

        except Exception as e:
            return {"error": str(e)}

    def _create_file(self, filename: str, content: str) -> Dict[str, Any]:
        """Create a file with content."""
        if not filename:
            return {"error": "Filename is required for create_file"}

        path = self._safe_path(filename)

        # Create parent directories if they don't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Write content to file
        path.write_text(content, encoding="utf-8")

        return {
            "status": "created",
            "path": str(path.relative_to(self.base_dir)),
            "size": len(content),
            "message": f"Created file: {filename}",
        }

    def _read_file(self, filename: str) -> Dict[str, Any]:
        """Read a file's content."""
        if not filename:
            return {"error": "Filename is required for read_file"}

        path = self._safe_path(filename)

        if not path.exists():
            return {"error": f"File not found: {filename}"}

        if not path.is_file():
            return {"error": f"Path is not a file: {filename}"}

        try:
            content = path.read_text(encoding="utf-8")
            return {
                "content": content,
                "path": str(path.relative_to(self.base_dir)),
                "size": len(content),
                "message": f"Read file: {filename}",
            }
        except Exception as e:
            return {"error": f"Failed to read file {filename}: {str(e)}"}

    def _list_files(self, directory: str = ".") -> Dict[str, Any]:
        """List files and directories."""
        path = self._safe_path(directory)

        if not path.exists():
            return {"error": f"Directory not found: {directory}"}

        if not path.is_dir():
            return {"error": f"Path is not a directory: {directory}"}

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

            return {
                "items": items,
                "directory": directory,
                "total": len(items),
                "message": f"Listed {len(items)} items in {directory}",
            }
        except Exception as e:
            return {"error": f"Failed to list directory {directory}: {str(e)}"}

    def _delete_file(self, filename: str) -> Dict[str, Any]:
        """Delete a file."""
        if not filename:
            return {"error": "Filename is required for delete_file"}

        path = self._safe_path(filename)

        if not path.exists():
            return {"error": f"File not found: {filename}"}

        if not path.is_file():
            return {"error": f"Path is not a file: {filename}"}

        try:
            path.unlink()
            return {
                "status": "deleted",
                "path": str(path.relative_to(self.base_dir)),
                "message": f"Deleted file: {filename}",
            }
        except Exception as e:
            return {"error": f"Failed to delete file {filename}: {str(e)}"}

    def get_schema(self) -> str:
        """Return tool call schema for LLM formatting."""
        return "file_manager(action='create_file|read_file|list_files|delete_file', filename='path/to/file', content='file content')"

    def get_usage_examples(self) -> List[str]:
        """Return example tool calls for LLM guidance."""
        return [
            "file_manager(action='create_file', filename='notes/plan.md', content='Build agent, ship blog, rest never.')",
            "file_manager(action='read_file', filename='notes/plan.md')",
            "file_manager(action='list_files', filename='notes')",
            "file_manager(action='delete_file', filename='notes/old_file.txt')",
        ]
