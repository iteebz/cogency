"""Shell command execution tool."""

import subprocess
import time
from pathlib import Path
from typing import Optional

from ...core.protocols import Tool, ToolResult
from ...core.result import Err, Ok, Result


class SystemShell(Tool):
    """shell execution with intelligence and context awareness."""

    # Categorized safe commands
    SAFE_COMMANDS = {
        # File operations
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
        # System
        "date",
        "whoami",
        "which",
        "env",
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

        command = command.strip()

        # Parse command safely
        try:
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

        # Working directory logic
        if sandbox:
            working_path = Path(".sandbox")
            working_path.mkdir(exist_ok=True)
        else:
            working_path = Path.cwd()

        # Execute with enhanced feedback
        try:
            start_time = time.time()

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

    def _get_command_suggestion(self, cmd: str) -> Optional[str]:
        """Get intelligent command suggestion for common mistakes."""
        return self.COMMAND_SUGGESTIONS.get(cmd)

    def _format_result(
        self,
        command: str,
        result: subprocess.CompletedProcess,
        execution_time: float,
        sandbox_path: Path,
    ) -> Result[ToolResult]:
        """Canonical shell result formatting - context in outcome, pure content."""

        if result.returncode == 0:
            # Build canonical outcome with context
            cmd_name = command.split()[0]
            rel_path = sandbox_path.name

            # Add timing if significant (AGENT PERFORMANCE SIGNAL)
            if execution_time > 0.1:
                outcome = f"Command executed: {cmd_name} ({rel_path}/ {execution_time:.1f}s)"
            else:
                outcome = f"Command executed: {cmd_name} ({rel_path}/)"

            # Pure content - just the output
            content_parts = []

            # Main output
            stdout = result.stdout.strip()
            if stdout:
                content_parts.append(stdout)

            # Warning for stderr even on success
            stderr = result.stderr.strip()
            if stderr:
                content_parts.append(f"Warnings:\n{stderr}")

            # Canonical outcome + pure content
            content = "\n".join(content_parts) if content_parts else None
            return Ok(ToolResult(outcome, content))

        # Failure formatting with helpful suggestions
        error_output = result.stderr.strip() or "Command failed"
        suggestion = self._get_error_suggestion(command, result.returncode, error_output)

        error_msg = f"✗ {command} (exit: {result.returncode})\n\n{error_output}"
        if suggestion:
            error_msg += f"\n\n* Suggestion: {suggestion}"

        return Err(error_msg)

    def _get_error_suggestion(
        self, command: str, exit_code: int, error_output: str
    ) -> Optional[str]:
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

        elif cmd in ["ls", "cat"] and "No such file" in error_output:
            return "Use 'list' tool to see available files, or 'pwd' to check current directory"

        elif exit_code == 1 and cmd == "python":
            return "Check syntax with 'cat filename.py' or run with 'python -c \"simple code\"'"

        return None
