import subprocess
from pathlib import Path

from ...core.protocols import Tool, ToolResult
from ..security import safe_execute, sanitize_shell_input


class SystemShell(Tool):
    """Execute shell commands with security validation."""

    name = "shell"
    description = "Execute system commands"
    schema = {"command": {}}

    def describe(self, args: dict) -> str:
        """Human-readable action description."""
        return f"Running {args.get('command', 'command')}"

    @safe_execute
    async def execute(
        self,
        command: str,
        timeout: int = 30,
        base_dir: str | None = None,
        access: str = "sandbox",
        **kwargs,
    ) -> ToolResult:
        """Execute command with proper security validation."""
        if not command or not command.strip():
            return ToolResult(outcome="Command cannot be empty", error=True)

        # Input validation and sanitization
        sanitized = sanitize_shell_input(command.strip())

        import shlex

        parts = shlex.split(sanitized)

        if not parts:
            return ToolResult(outcome="Empty command after parsing", error=True)

        # Set working directory based on access level
        if access == "sandbox":
            from ...lib.paths import Paths

            working_path = Paths.sandbox(base_dir=base_dir)
            working_path.mkdir(exist_ok=True)
        else:
            # project or system access
            working_path = Path(base_dir) if base_dir else Path.cwd()

        try:
            result = subprocess.run(
                parts, cwd=str(working_path), capture_output=True, text=True, timeout=timeout
            )

            if result.returncode == 0:
                content_parts = []

                if result.stdout.strip():
                    content_parts.append(result.stdout.strip())

                if result.stderr.strip():
                    content_parts.append(f"Warnings:\n{result.stderr.strip()}")

                content = "\n".join(content_parts) if content_parts else ""
                outcome = "Command completed"

                return ToolResult(outcome=outcome, content=content)
            error_output = result.stderr.strip() or "Command failed"
            return ToolResult(
                outcome=f"Command failed (exit {result.returncode}): {error_output}", error=True
            )

        except subprocess.TimeoutExpired:
            return ToolResult(outcome=f"Command timed out after {timeout} seconds", error=True)
        except FileNotFoundError:
            return ToolResult(outcome=f"Command not found: {parts[0]}", error=True)
