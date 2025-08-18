"""Shell: Safe command execution in sandbox."""

import subprocess
import time
from pathlib import Path

from ..core.protocols import Tool
from ..lib.result import Err, Ok, Result


class Shell(Tool):
    """Execute safe commands in sandbox."""

    # Allowlist of safe commands
    SAFE_COMMANDS = {
        "ls",
        "pwd",
        "cat",
        "echo",
        "wc",
        "grep",
        "head",
        "tail",
        "mkdir",
        "touch",
        "cp",
        "mv",
        "rm",
        "python",
        "python3",
        "node",
        "npm",
        "pip",
        "git",
    }

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return (
            f"Execute safe commands in sandbox. Available: {', '.join(sorted(self.SAFE_COMMANDS))}"
        )

    async def execute(self, command: str) -> Result[str, str]:
        # Parse and validate command
        parts = command.strip().split()
        if not parts:
            return Err("Empty command")

        cmd = parts[0]
        if cmd not in self.SAFE_COMMANDS:
            return Err(
                f"Command '{cmd}' not allowed. Available: {', '.join(sorted(self.SAFE_COMMANDS))}"
            )

        # Ensure sandbox exists
        Path(".sandbox").mkdir(exist_ok=True)

        try:
            start = time.time()

            # Execute with shell=False for security
            result = subprocess.run(
                parts, cwd=".sandbox", capture_output=True, text=True, timeout=30
            )

            duration = time.time() - start

            if result.returncode == 0:
                output = result.stdout.strip()
                stderr = result.stderr.strip()

                feedback = f"{command} (exit: 0, time: {duration:.1f}s)"
                if output:
                    feedback += f"\n\n{output}"
                if stderr:
                    feedback += f"\n\nSTDERR:\n{stderr}"

                return Ok(feedback)

            error = result.stderr.strip()
            return Err(f"{command} (exit: {result.returncode})\n\n{error}")

        except subprocess.TimeoutExpired:
            return Err(f"Command timed out: {command} (30s limit)")
        except FileNotFoundError:
            return Err(f"Command not found: {cmd}")
        except Exception as e:
            return Err(f"Shell error: {str(e)}")
