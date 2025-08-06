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
    path: str = ""
    content: Optional[str] = None
    line: Optional[int] = None
    start: Optional[int] = None
    end: Optional[int] = None


@tool
class Files(Tool):
    """File operations within a safe base directory."""

    def __init__(self, base_dir: str = None):
        from ..config import PathsConfig

        if base_dir is None:
            base_dir = PathsConfig().sandbox
        super().__init__(
            name="files",
            description="Create, read, edit and manage complete code files with full implementations.",
            schema="files(action: str, path: str = '', content: str = None, line: int = None, start: int = None, end: int = None)",
            emoji="📁",
            args=FilesArgs,
            examples=[
                '{"name": "files", "args": {"action": "create", "path": "app.py", "content": "from fastapi import FastAPI\\n\\napp = FastAPI()\\n\\n@app.get(\\"/\\")\\nasync def root():\\n    return {\\"message\\": \\"Hello World\\"}"}}',
                '{"name": "files", "args": {"action": "create", "path": "models.py", "content": "from pydantic import BaseModel\\nfrom typing import List, Optional\\n\\nclass User(BaseModel):\\n    id: int\\n    name: str\\n    email: Optional[str] = None"}}',
                '{"name": "files", "args": {"action": "read", "path": "app.py"}}',
                '{"name": "files", "args": {"action": "edit", "path": "app.py", "line": 5, "content": "@app.get(\\"/users\\")"}}',
                '{"name": "files", "args": {"action": "list", "path": "src"}}',
            ],
            rules=[
                'CRITICAL: Use JSON format: {"name": "files", "args": {"action": "...", ...}}. Never use function-call syntax.',
                "CRITICAL: When creating files, provide complete, functional code implementations; never placeholder comments or stubs.",
                "Start with focused, core functionality - avoid overly long files in initial creation.",
                "Include proper imports, error handling, and production-ready code.",
                "For Python: Include proper type hints, docstrings, and follow PEP 8.",
                "Generate working, executable code that solves the specified requirements.",
                "For complex features, create smaller focused files and build incrementally.",
                "For 'edit' action, specify 'path' and either 'line' (for single line) or 'start' and 'end' (for range).",
                "For 'list' action, 'path' can be a directory path; defaults to current directory.",
                "File paths are relative to the tool's working directory (e.g., 'app.py', 'src/module.py', 'models/user.py').",
            ],
        )
        # Use base class formatting with templates
        self.arg_key = "path"
        self.human_template = "{result}"
        self.agent_template = "{action} {path}"

        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_path(self, rel_path: str) -> Path:
        """Ensure path is within base directory."""
        if not rel_path:
            raise ValueError("Path cannot be empty")

        # Normalize path: strip sandbox prefix if already included
        # This fixes the double-sandbox-path bug
        normalized_path = rel_path
        try:
            # Only normalize if base_dir is relative to current working directory
            sandbox_prefix = str(self.base_dir.relative_to(Path.cwd()))
            if rel_path.startswith(sandbox_prefix + "/"):
                normalized_path = rel_path[len(sandbox_prefix) + 1 :]
            elif rel_path.startswith(sandbox_prefix):
                normalized_path = rel_path[len(sandbox_prefix) :].lstrip("/")
        except ValueError:
            # base_dir is not relative to cwd (e.g., temp directory) - use path as-is
            pass

        path = (self.base_dir / normalized_path).resolve()

        if not str(path).startswith(str(self.base_dir)):
            raise ValueError(f"Unsafe path access: {rel_path}")

        return path

    async def run(
        self,
        action: str,
        path="",
        content="",
        line: int = None,
        start: int = None,
        end: int = None,
    ) -> Dict[str, Any]:
        """Execute file operations."""
        try:
            if action == "create":
                path = self._safe_path(path)
                if path.exists():
                    return Result.fail(
                        f"File already exists: {path}. Please specify if you want to overwrite, rename, or choose a different approach."
                    )

                # Security: validate file content using centralized patterns
                from cogency.security import secure_tool

                security_result = secure_tool(content or "")
                if not security_result.safe:
                    return Result.fail(f"Security violation: {security_result.message}")

                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return Result.ok(
                    {
                        "result": f"Created file: {path.relative_to(self.base_dir)}",
                        "full_path": str(path),
                        "size": len(content),
                    }
                )

            elif action == "read":
                path = self._safe_path(path)
                if not path.exists():
                    return Result.fail(f"File not found: {path}")

                content = path.read_text(encoding="utf-8")
                return Result.ok(
                    {
                        "result": f"Read file: {path}",
                        "content": content,
                        "size": len(content),
                    }
                )

            elif action == "edit":
                path = self._safe_path(path)
                if not path.exists():
                    return Result.fail(f"File not found: {path}")

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

                # Security: validate edited content using centralized patterns
                new_content = "\n".join(lines)
                from cogency.security import secure_tool

                security_result = secure_tool(new_content)
                if not security_result.safe:
                    return Result.fail(f"Security violation: {security_result.message}")

                path.write_text(new_content, encoding="utf-8")
                return Result.ok(
                    {
                        "result": f"{result_msg} in {path}",
                        "size": len(new_content),
                    }
                )

            elif action == "list":
                path = self._safe_path(path if path else ".")
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

            else:
                return Result.fail(f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"File operation failed: {e}")
            return Result.fail(f"File operation failed: {str(e)}")
