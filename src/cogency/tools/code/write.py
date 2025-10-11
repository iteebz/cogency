from ...core.config import Access
from ...core.protocols import Tool, ToolResult
from ..security import resolve_file, safe_execute


class Write(Tool):
    """Write file."""

    name = "write"
    description = "Write file. Fails if exists - use edit instead."
    schema = {"file": {}, "content": {}}

    def describe(self, args: dict) -> str:
        return f"Writing {args.get('file', 'file')}"

    @safe_execute
    async def execute(
        self,
        file: str,
        content: str,
        sandbox_dir: str = ".cogency/sandbox",
        access: Access = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not file:
            return ToolResult(outcome="File cannot be empty", error=True)

        file_path = resolve_file(file, access, sandbox_dir)

        if file_path.exists():
            return ToolResult(
                outcome=(
                    f"File {file} already exists. "
                    'Use edit (old="...") or edit (old="") to overwrite.'
                ),
                error=True,
            )

        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        lines = content.count("\n") + 1 if content else 0
        return ToolResult(outcome=f"Wrote {file} (+{lines}/-0)")
