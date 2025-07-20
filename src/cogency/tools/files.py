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
            description="Manage files and directories - create, read, list, and delete files safely.",
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

    async def run(self, action: str, filename: str = "", content: str = "") -> Dict[str, Any]:
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
        return "files(action=REQUIRED, filename=REQUIRED, content=optional) - action must be: create|read|list|delete"

    def get_usage_examples(self) -> List[str]:
        return [
            "files(action='create', filename='notes/plan.md', content='Build agent, ship blog, rest never.')",
            "files(action='read', filename='notes/plan.md')",
            "files(action='list', filename='notes')",
            "files(action='delete', filename='notes/old_file.txt')",
        ]
    
    def format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display."""
        from cogency.messaging import _truncate
        action, filename = params.get("action"), params.get("filename")
        if action and filename:
            return f"({action}, {_truncate(filename, 25)})"
        return f"({_truncate(filename or '', 30)})" if filename else ""
