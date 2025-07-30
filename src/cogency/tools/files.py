"""File operations tool - read, write, list files with validation and error handling."""

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class FilesArgs:
    action: str
    filename: str = ""  # Default to empty for list action
    content: Optional[str] = None
    line: Optional[int] = None
    start: Optional[int] = None
    end: Optional[int] = None


@tool
class Files(Tool):
    """File operations within a safe base directory."""

    # Template-based formatting - shows action and filename
    param_key = "filename"

    def __init__(self, base_dir: str = "sandbox"):
        super().__init__(
            name="files",
            description="Create, read, edit and manage complete code files with full implementations.",
            schema="files(action: str, filename: str = '', content: str = None, line: int = None, start: int = None, end: int = None)",
            emoji="📁",
            params=FilesArgs,
            examples=[
                "files(action='create', filename='app.py', content='from fastapi import FastAPI\\n\\napp = FastAPI()\\n\\n@app.get(\"/\")\\nasync def root():\\n    return {\"message\": \"Hello World\"}')",
                "files(action='create', filename='models.py', content='from pydantic import BaseModel\\nfrom typing import List, Optional\\n\\nclass User(BaseModel):\\n    id: int\\n    name: str\\n    email: Optional[str] = None')",
                "files(action='read', filename='app.py')",
                "files(action='edit', filename='app.py', line=5, content='@app.get(\"/users\")')",
                "files(action='list', filename='src')",
            ],
            rules=[
                "CRITICAL: When creating files, provide complete, functional code implementations; never placeholder comments or stubs.",
                "Start with focused, core functionality - avoid overly long files in initial creation.",
                "Include proper imports, error handling, and production-ready code.",
                "For Python: Include proper type hints, docstrings, and follow PEP 8.",
                "Generate working, executable code that solves the specified requirements.",
                "For complex features, create smaller focused files and build incrementally.",
                "For 'edit' action, specify 'filename' and either 'line' (for single line) or 'start' and 'end' (for range).",
                "For 'list' action, 'filename' can be a directory path; defaults to current directory.",
                "File paths are relative to the tool's working directory (e.g., 'app.py', 'src/module.py', 'models/user.py').",
            ],
        )
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, rel_path: str) -> Path:
        """Ensure path is within base directory."""
        if not rel_path:
            raise ValueError("Path cannot be empty")

        path = (self.base_dir / rel_path).resolve()

        if not str(path).startswith(str(self.base_dir)):
            raise ValueError(f"Unsafe path access: {rel_path}")

        return path

    def _suggest_similar_files(self, target: str) -> list[str]:
        """Find similar files for typo correction."""
        import difflib

        # Get all files in base directory recursively
        all_files = []
        try:
            for path in self.base_dir.rglob("*"):
                if path.is_file():
                    rel_path = path.relative_to(self.base_dir)
                    all_files.append(str(rel_path))
        except Exception:
            return []

        # Find close matches (similarity > 0.6)
        matches = difflib.get_close_matches(target, all_files, n=3, cutoff=0.6)
        return matches

    async def run(
        self,
        action: str,
        filename: str = "",
        content: str = "",
        line: int = None,
        start: int = None,
        end: int = None,
    ) -> Dict[str, Any]:
        """Execute file operations."""
        try:
            if action == "create":
                path = self._safe_path(filename)
                if path.exists():
                    return Result.fail(
                        f"File already exists: {filename}. Read it first with files(action='read', filename='{filename}') before creating."
                    )
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return Result.ok({"result": f"Created file: {filename}", "size": len(content)})

            elif action == "read":
                path = self._safe_path(filename)
                if not path.exists():
                    # Try fuzzy matching for common mistakes
                    suggestions = self._suggest_similar_files(filename)
                    if suggestions:
                        return Result.fail(
                            f"File not found: {filename}. Did you mean: {', '.join(suggestions)}?"
                        )
                    else:
                        return Result.fail(f"File not found: {filename}")

                content = path.read_text(encoding="utf-8")
                return Result.ok(
                    {
                        "result": f"Read file: {filename}",
                        "content": content,
                        "size": len(content),
                    }
                )

            elif action == "edit":
                path = self._safe_path(filename)
                if not path.exists():
                    suggestions = self._suggest_similar_files(filename)
                    if suggestions:
                        return Result.fail(
                            f"File not found: {filename}. Did you mean: {', '.join(suggestions)}?"
                        )
                    else:
                        return Result.fail(f"File not found: {filename}")

                lines = path.read_text(encoding="utf-8").splitlines()

                if line is not None:
                    # Single line edit
                    if line < 1 or line > len(lines):
                        return Result.fail(f"Line {line} out of range (1-{len(lines)})")
                    lines[line - 1] = content
                    result_msg = f"Edited line {line}"

                elif start is not None and end is not None:
                    # Range edit
                    if (
                        start < 1
                        or end < 1
                        or start > len(lines)
                        or end > len(lines)
                        or start > end
                    ):
                        return Result.fail(
                            f"Invalid range {start}-{end} (file has {len(lines)} lines)"
                        )
                    # Replace lines start to end (inclusive) with new content
                    new_lines = content.splitlines() if content else []
                    lines[start - 1 : end] = new_lines
                    result_msg = f"Edited lines {start}-{end}"

                else:
                    # Full file replace
                    lines = content.splitlines()
                    result_msg = "Replaced entire file"

                new_content = "\n".join(lines)
                path.write_text(new_content, encoding="utf-8")
                return Result.ok(
                    {
                        "result": f"{result_msg} in {filename}",
                        "size": len(new_content),
                    }
                )

            elif action == "list":
                path = self._safe_path(filename if filename else ".")
                items = []
                for item in sorted(path.iterdir()):
                    items.append(
                        {
                            "name": item.name,
                            "type": "directory" if item.is_dir() else "file",
                            "size": item.stat().st_size if item.is_file() else None,
                        }
                    )
                return Result.ok({"result": f"Listed {len(items)} items", "items": items})

            elif action == "delete":
                path = self._safe_path(filename)
                path.unlink()
                return Result.ok({"result": f"Deleted file: {filename}"})

            else:
                return Result.fail(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"File operation failed: {e}")
            return Result.fail(str(e))
