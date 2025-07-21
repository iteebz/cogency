from pathlib import Path
from typing import Any, Dict, List

from cogency.tools.base import BaseTool
# Error handling now in BaseTool.execute() - no decorators needed


from cogency.tools.registry import tool

@tool
class Files(BaseTool):
    """File operations within a safe base directory."""

    def __init__(self, base_dir: str = ".cogency/sandbox"):
        super().__init__(
            name="files",
            description="Manage files and directories - create, read, edit, list, and delete files safely.",
            emoji="📁"
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

    async def run(self, action: str, filename: str = "", content: str = "", line: int = None, start: int = None, end: int = None) -> Dict[str, Any]:
        """Execute file operations."""
        try:
            if action == "create":
                path = self._safe_path(filename)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content, encoding="utf-8")
                return {"result": f"Created file: {filename}", "size": len(content)}
            
            elif action == "read":
                path = self._safe_path(filename)
                content = path.read_text(encoding="utf-8")
                return {"result": f"Read file: {filename}", "content": content, "size": len(content)}
            
            elif action == "edit":
                path = self._safe_path(filename)
                if not path.exists():
                    return {"error": f"File not found: {filename}"}
                
                lines = path.read_text(encoding="utf-8").splitlines()
                
                if line is not None:
                    # Single line edit
                    if line < 1 or line > len(lines):
                        return {"error": f"Line {line} out of range (1-{len(lines)})"}
                    lines[line - 1] = content
                    result_msg = f"Edited line {line}"
                
                elif start is not None and end is not None:
                    # Range edit
                    if start < 1 or end < 1 or start > len(lines) or end > len(lines) or start > end:
                        return {"error": f"Invalid range {start}-{end} (file has {len(lines)} lines)"}
                    # Replace lines start to end (inclusive) with new content
                    new_lines = content.splitlines() if content else []
                    lines[start-1:end] = new_lines
                    result_msg = f"Edited lines {start}-{end}"
                
                else:
                    # Full file replace
                    lines = content.splitlines()
                    result_msg = "Replaced entire file"
                
                new_content = "\n".join(lines)
                path.write_text(new_content, encoding="utf-8")
                return {"result": f"{result_msg} in {filename}", "size": len(new_content)}
            
            elif action == "list":
                path = self._safe_path(filename if filename else ".")
                items = []
                for item in sorted(path.iterdir()):
                    items.append({
                        "name": item.name,
                        "type": "directory" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None
                    })
                return {"result": f"Listed {len(items)} items", "items": items}
            
            elif action == "delete":
                path = self._safe_path(filename)
                path.unlink()
                return {"result": f"Deleted file: {filename}"}
            
            else:
                return {"error": f"Unknown action: {action}"}
                
        except Exception as e:
            return {"error": str(e)}

    def get_schema(self) -> str:
        return "files(action='create|read|edit|list|delete', filename='path', content='text', line=int, start=int, end=int)"

    def get_usage_examples(self) -> List[str]:
        return [
            "files(action='create', filename='notes/plan.md', content='Build agent, ship blog, rest never.')",
            "files(action='read', filename='notes/plan.md')",
            "files(action='edit', filename='app.py', line=10, content='new_line')",
            "files(action='edit', filename='app.py', start=5, end=8, content='new\\nlines')",
            "files(action='list', filename='notes')",
            "files(action='delete', filename='notes/old_file.txt')",
        ]
    
    def format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display."""
        from cogency.utils.formatting import truncate
        action, filename = params.get("action"), params.get("filename")
        if action and filename:
            return f"({action}, {truncate(filename, 25)})"
        return f"({truncate(filename or '', 30)})" if filename else ""
