"""Shell: Execute shell commands in sandbox."""

import subprocess
import time

from .base import Tool


class Shell(Tool):
    """Execute shell commands."""

    @property
    def name(self) -> str:
        return "shell"

    @property
    def description(self) -> str:
        return "Execute shell command in sandbox. Args: command (str)"

    async def execute(self, command: str) -> str:
        try:
            start = time.time()

            result = subprocess.run(
                command, shell=True, cwd=".sandbox", capture_output=True, text=True, timeout=30
            )

            duration = time.time() - start

            if result.returncode == 0:
                output = result.stdout.strip()
                stderr = result.stderr.strip()

                feedback = f"✅ Command: {command} (exit: 0, time: {duration:.1f}s)"
                if output:
                    feedback += f"\n\n{output}"
                if stderr:
                    feedback += f"\n\nSTDERR:\n{stderr}"

                return feedback
            error = result.stderr.strip()
            return f"❌ Command: {command} (exit: {result.returncode})\n\n{error}"

        except subprocess.TimeoutExpired:
            return f"❌ Command timed out: {command} (30s limit)"
        except Exception as e:
            return f"❌ Shell error: {str(e)}"
