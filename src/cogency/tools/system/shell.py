"""Shell command execution tool."""

import subprocess
import time
from pathlib import Path

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result
from ..security import sanitize_shell_input, timeout_context


class SystemShell(Tool):
    """shell execution with intelligence and context awareness."""

    # Categorized safe commands - rely on semantic security for dangerous usage
    SAFE_COMMANDS = {
        # File operations - semantic security handles dangerous paths
        "ls",
        "pwd",
        "cat",
        "head",
        "tail",
        "wc",
        "grep",
        "find",
        "mkdir",
        "touch",
        "cp",
        "mv",
        "rm",
        "chmod",
        # Text processing
        "echo",
        "sort",
        "tr",
        "cut",
        "uniq",
        "sed",
        "awk",
        # Development
        "python",
        "python3",
        "node",
        "npm",
        "pip",
        "git",
        # System info - semantic security handles reconnaissance usage
        "date",
        "whoami",
        "which",
        "env",
        # DANGEROUS commands - let semantic security handle them
        "ps",  # Process enumeration - semantic security blocks malicious usage
        "netstat",  # Network reconnaissance - semantic security blocks
        "history",  # Command history - semantic security blocks credential harvesting
    }

    # Command suggestions for common mistakes
    COMMAND_SUGGESTIONS = {
        "python3": "python",
        "nodejs": "node",
        "list": "ls",
        "copy": "cp",
        "move": "mv",
        "remove": "rm",
        "delete": "rm",
    }

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute system commands"

    @property
    def schema(self) -> dict:
        return {"command": {}}

    async def execute(self, command: str, sandbox: bool = True, **kwargs) -> Result[ToolResult]:
        """Execute command with enhanced intelligence and context."""
        if not command or not command.strip():
            return Err("Command cannot be empty")

        # Sanitize command input using proper escaping
        try:
            command = sanitize_shell_input(command.strip())
            import shlex

            parts = shlex.split(command)
        except ValueError as e:
            return Err(f"Invalid command syntax: {str(e)}")

        if not parts:
            return Err("Empty command after parsing")

        cmd = parts[0]

        # Security validation with suggestions
        if cmd not in self.SAFE_COMMANDS:
            suggestion = self._get_command_suggestion(cmd)
            available = ", ".join(sorted(self.SAFE_COMMANDS))

            if suggestion:
                return Err(
                    f"Command '{cmd}' not allowed. Did you mean '{suggestion}'? Available: {available}"
                )
            return Err(f"Command '{cmd}' not allowed. Available: {available}")

        # Argument validation - semantic security handles most cases, catch obvious system access
        if not self._validate_command_safety(parts, sandbox):
            return Err(f"Command arguments contain system paths or dangerous operations: {command}")

        # Working directory logic
        if sandbox:
            from ...lib.storage import Paths

            working_path = Paths.sandbox()
            working_path.mkdir(exist_ok=True)
        else:
            working_path = Path.cwd()

        # Execute with enhanced feedback and timeout protection
        try:
            start_time = time.time()

            with timeout_context(30):
                result = subprocess.run(
                    parts, cwd=str(working_path), capture_output=True, text=True, timeout=30
                )

            execution_time = time.time() - start_time

            # Format intelligent output
            return self._format_result(command, result, execution_time, working_path)

        except subprocess.TimeoutExpired:
            return Err(f"Command timed out after 30 seconds: {command}")
        except FileNotFoundError:
            return Err(f"Command not found: {cmd}")
        except Exception as e:
            return Err(f"Execution error: {str(e)}")

    def _get_command_suggestion(self, cmd: str) -> str | None:
        """Get intelligent command suggestion for common mistakes."""
        return self.COMMAND_SUGGESTIONS.get(cmd)

    def _validate_command_safety(self, parts: list, sandbox: bool) -> bool:
        """Validate command arguments for obvious system access patterns.

        Semantic security handles sophisticated attacks - this catches basic patterns.
        """
        full_command = " ".join(parts)

        # System paths that should never be accessed
        dangerous_paths = [
            "/etc/",
            "/bin/",
            "/sbin/",
            "/usr/bin/",
            "/System/",
            "/etc/passwd",
            "/etc/hosts",
            "/etc/shadow",
            "~/.ssh/",
            "~/.bashrc",
            "~/.profile",
        ]

        # Check for dangerous path patterns
        for path in dangerous_paths:
            if path in full_command:
                return False

        # Additional validation for specific commands
        cmd = parts[0]

        if cmd == "find" and len(parts) > 1 and (parts[1] == "/" or parts[1].startswith("/")):
            # Block filesystem-wide searches
            return False

        if cmd == "cat" and len(parts) > 1:
            # Block system file reading
            for arg in parts[1:]:
                if arg.startswith("/etc/") or arg.startswith("/bin/"):
                    return False

        return True

    def _format_result(
        self,
        command: str,
        result: subprocess.CompletedProcess,
        execution_time: float,
        sandbox_path: Path,
    ) -> Result[ToolResult]:
        """Shell result formatting - context in outcome, pure content."""

        if result.returncode == 0:
            cmd_name = command.split()[0]

            # Add timing if significant (AGENT PERFORMANCE SIGNAL)
            if execution_time > 0.1:
                pass
            else:
                pass

            content_parts = []

            stdout = result.stdout.strip()
            if stdout:
                content_parts.append(stdout)

            # Warning for stderr even on success
            stderr = result.stderr.strip()
            if stderr:
                content_parts.append(f"Warnings:\n{stderr}")

            "\n".join(content_parts) if content_parts else ""

            return Ok(
                ToolResult(
                    display=f"ran {cmd_name}: exit {result.returncode}",
                    raw_data={
                        "command": command,
                        "exit_code": result.returncode,
                        "stdout": result.stdout,
                        "stderr": result.stderr,
                        "execution_time": execution_time,
                        "working_directory": str(sandbox_path),
                    },
                )
            )

        # Failure formatting with helpful suggestions
        error_output = result.stderr.strip() or "Command failed"
        suggestion = self._get_error_suggestion(command, result.returncode, error_output)

        error_msg = f"✗ {command} (exit: {result.returncode})\n\n{error_output}"
        if suggestion:
            error_msg += f"\n\n* Suggestion: {suggestion}"

        return Err(error_msg)

    def _get_error_suggestion(self, command: str, exit_code: int, error_output: str) -> str | None:
        """Provide intelligent suggestions for command failures."""
        cmd_parts = command.split()
        cmd = cmd_parts[0]

        if "not found" in error_output.lower():
            if cmd == "python":
                return "Try 'python3' or check if Python is installed"
            if cmd in ["npm", "node"]:
                return "Node.js may not be available in this environment"

        elif cmd == "git" and "not a git repository" in error_output.lower():
            return "Initialize git repository with 'git init' first"

        elif cmd == "ls" and "No such file" in error_output:
            return "Use 'list' tool to see available files, or 'pwd' to check current directory"

        elif exit_code == 1 and cmd == "python":
            return "Check syntax with 'read' tool or run with 'python -c \"simple code\"'"

        return None
