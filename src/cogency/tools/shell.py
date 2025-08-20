"""Enhanced Shell: Intelligent command execution with context awareness."""

import subprocess
import time
from pathlib import Path
from typing import Optional

from ..core.protocols import Tool
from ..lib.result import Err, Ok, Result


class Shell(Tool):
    """Enhanced shell execution with intelligence and context awareness."""

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
        return "Execute commands with intelligent feedback and suggestions. Args: command (str)"

    @property
    def schema(self) -> dict:
        return {
            "command": {"type": "str", "required": True, "description": "Shell command to execute"}
        }

    @property
    def examples(self) -> list[dict]:
        return [
            {"task": "List directory contents", "call": {"command": "ls -la"}},
            {"task": "Run Python script", "call": {"command": "python hello.py"}},
            {"task": "Create directory", "call": {"command": "mkdir new_folder"}},
            {"task": "Check Git status", "call": {"command": "git status"}},
            {"task": "Count lines in file", "call": {"command": "wc -l file.txt"}},
        ]

    async def execute(self, command: str) -> Result[str, str]:
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

        # Ensure sandbox exists
        sandbox_path = Path(".sandbox")
        sandbox_path.mkdir(exist_ok=True)

        # Execute with enhanced feedback
        try:
            start_time = time.time()

            result = subprocess.run(
                parts, cwd=str(sandbox_path), capture_output=True, text=True, timeout=30
            )

            execution_time = time.time() - start_time

            # Format intelligent output
            return self._format_result(command, result, execution_time, sandbox_path)

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
    ) -> Result[str, str]:
        """Format command result with intelligent context."""

        if result.returncode == 0:
            # Success formatting
            output_parts = []

            # Command header with context
            header = f"✓ {command}"
            if execution_time > 0.1:  # Only show time if significant
                header += f" ({execution_time:.1f}s)"
            output_parts.append(header)

            # Add working directory context for relevant commands
            if command.startswith(("ls", "pwd", "find")):
                rel_path = sandbox_path.name
                output_parts.append(f"Working directory: {rel_path}/")

            # Main output
            stdout = result.stdout.strip()
            if stdout:
                output_parts.append(f"\n{stdout}")

            # Warning for stderr even on success
            stderr = result.stderr.strip()
            if stderr:
                output_parts.append(f"\nWarnings:\n{stderr}")

            # Add helpful context for specific commands
            context = self._get_command_context(command, stdout)
            if context:
                output_parts.append(f"\n💡 {context}")

            return Ok("\n".join(output_parts))

        # Failure formatting with helpful suggestions
        error_output = result.stderr.strip() or "Command failed"
        suggestion = self._get_error_suggestion(command, result.returncode, error_output)

        error_msg = f"✗ {command} (exit: {result.returncode})\n\n{error_output}"
        if suggestion:
            error_msg += f"\n\n💡 Suggestion: {suggestion}"

        return Err(error_msg)

    def _get_command_context(self, command: str, output: str) -> Optional[str]:
        """Provide intelligent context for command results."""
        cmd_parts = command.split()
        cmd = cmd_parts[0]

        if cmd == "ls" and output:
            file_count = len(output.split("\n"))
            return f"Found {file_count} items. Use 'ls -la' for details or 'list' tool for structured view."

        if cmd == "python" and "error" not in output.lower():
            return "Python executed successfully. Use 'cat filename.py' to view source code."

        if cmd == "git" and "status" in command:
            if "nothing to commit" in output:
                return "Repository is clean. Use 'git log --oneline -5' to see recent commits."
            return "Changes detected. Use 'git add .' to stage changes."

        if cmd == "find" and output:
            result_count = len(output.split("\n"))
            return f"Found {result_count} matches. Use 'cat filename' to view file contents."

        return None

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
