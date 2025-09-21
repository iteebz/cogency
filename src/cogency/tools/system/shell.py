"""Shell command execution with security validation and sandbox isolation."""

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
        self, command: str, sandbox: bool = True, timeout: int = 30, **kwargs
    ) -> ToolResult:
        """Execute command with proper security validation."""
        if not command or not command.strip():
            return ToolResult(outcome="Command cannot be empty")

        # Input validation and sanitization
        sanitized = sanitize_shell_input(command.strip())

        import shlex

        parts = shlex.split(sanitized)

        if not parts:
            return ToolResult(outcome="Empty command after parsing")

        # Set working directory based on sandbox mode
        if sandbox:
            from ...lib.paths import Paths

            working_path = Paths.sandbox()
            working_path.mkdir(exist_ok=True)
        else:
            working_path = Path.cwd()

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
            return ToolResult(outcome=f"Command failed (exit {result.returncode}): {error_output}")

        except subprocess.TimeoutExpired:
            return ToolResult(outcome=f"Command timed out after {timeout} seconds")
        except FileNotFoundError:
            return ToolResult(outcome=f"Command not found: {parts[0]}")
