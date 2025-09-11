"""File writing tool."""

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from ..security import resolve_path_safely


class FileWrite(Tool):
    """File writing with intelligent feedback and context awareness."""

    @property
    def name(self) -> str:
        return "write"

    @property
    def description(self) -> str:
        return "Write content to file"

    @property
    def schema(self) -> dict:
        return {"file": {}, "content": {}}

    async def execute(
        self, file: str, content: str, sandbox: bool = True, **kwargs
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

            # Write with UTF-8 encoding
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            outcome = f"File written to {file}"
            return Ok(ToolResult(outcome))

        except ValueError as e:
            return Err(f"Security violation: {str(e)}")
        except Exception as e:
            return Err(f"Failed to write '{file}': {str(e)}")
