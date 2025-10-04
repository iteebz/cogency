import glob
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
        sandbox_dir: str = ".cogency/sandbox",
        access: str = "sandbox",
        **kwargs,
    ) -> ToolResult:
        if not command or not command.strip():
            return ToolResult(outcome="Command cannot be empty", error=True)

        sanitized = sanitize_shell_input(command.strip())

        import shlex

        parts = shlex.split(sanitized)

        if not parts:
            return ToolResult(outcome="Empty command after parsing", error=True)

        if access == "sandbox":
            working_path = Path(sandbox_dir)
            working_path.mkdir(parents=True, exist_ok=True)
        else:
            working_path = Path.cwd()

        expanded_parts = [parts[0]]
        for arg in parts[1:]:
            if any(char in arg for char in "*?["):
                # Expand simple glob patterns relative to the working directory
                matches = glob.glob(arg, root_dir=str(working_path))
                if matches:
                    expanded_parts.extend(matches)
                    continue
            expanded_parts.append(arg)

        try:
            result = subprocess.run(
                expanded_parts,
                cwd=str(working_path),
                capture_output=True,
                text=True,
                timeout=timeout,
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
