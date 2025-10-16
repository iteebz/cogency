from ..core.config import Access
from ..core.protocols import Tool, ToolResult
from ..core.security import resolve_file, safe_execute


class Write(Tool):
    """Write file."""

    name = "write"
    description = "Write file. Can be configured to overwrite."
    schema = {"file": {}, "content": {}, "overwrite": {"type": "boolean", "default": False}}

    def describe(self, args: dict) -> str:
        return f"Writing {args.get('file', 'file')}"

    @safe_execute
    async def execute(
        self,
        file: str,
        content: str,
        overwrite: bool = False,
        sandbox_dir: str = ".cogency/sandbox",
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty", error=True)

        file_path = resolve_file(file, access, sandbox_dir)

        if file_path.exists() and not overwrite:
            return ToolResult(
                outcome=f"File '{file}' already exists. Try: overwrite=True to replace, or choose different name.",
                error=True,
            )

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        lines = content.count("\n") + 1 if content else 0
        preview = content[:200] + ("..." if len(content) > 200 else "")
        return ToolResult(outcome=f"Wrote {file} (+{lines}/-0)", content=preview)
