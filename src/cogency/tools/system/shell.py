"""Shell command execution tool."""

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
    async def execute(self, command: str, sandbox: bool = True, **kwargs) -> ToolResult:
        """Execute command with proper security validation."""
        if not command or not command.strip():
            return ToolResult(outcome="Command cannot be empty")

        # Security validation handled by security layer
        sanitized = sanitize_shell_input(command.strip())

        import shlex

        parts = shlex.split(sanitized)

        if not parts:
            return ToolResult(outcome="Empty command after parsing")

        # Working directory
        if sandbox:
            from ...lib.storage import Paths

            working_path = Paths.sandbox()
            working_path.mkdir(exist_ok=True)
        else:
            working_path = Path.cwd()

        # Execute
        try:
            result = subprocess.run(
                parts, cwd=str(working_path), capture_output=True, text=True, timeout=30
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
            return ToolResult(outcome=f"Command failed (exit {result.returncode}): {error_output}")

        except subprocess.TimeoutExpired:
            return ToolResult(outcome="Command timed out after 30 seconds")
        except FileNotFoundError:
            return ToolResult(outcome=f"Command not found: {parts[0]}")
