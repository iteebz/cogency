"""Shell tool for safe system command execution - SANDBOXED & TIMEOUT PROTECTED."""

import asyncio
import logging
import os
import shlex
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional

from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class ShellArgs:
    command: str
    timeout: int = 30
    working_dir: Optional[str] = None
    env: Optional[Dict[str, str]] = None


@tool
class Shell(Tool):
    """Execute system commands safely with timeout and basic sandboxing."""

    def __init__(self, default_working_dir: str = "sandbox"):
        super().__init__(
            name="shell",
            description="Run shell commands and scripts - for executing files, running programs, terminal operations",
            schema="shell(command: str, timeout: int = 30, working_dir: str = None, env: dict = None)",
            emoji="💻",
            params=ShellArgs,
            examples=[
                "shell(command='ls -la')",
                "shell(command='pwd')",
                "shell(command='echo \"Hello World\"')",
                "shell(command='python --version')",
                "shell(command='git status', working_dir='/path/to/repo')",
                "shell(command='python -m pip install -r requirements.txt')",
            ],
            rules=[
                "Prefer 'python -m <module>' for executing Python modules (e.g., 'python -m pip', 'python -m pytest').",
                "Avoid using commands that modify system state or delete files (e.g., 'rm', 'sudo').",
                "Blocked commands include: rm, rmdir, del, format, fdisk, mkfs, dd, shutdown, reboot, halt, poweroff, init, su, sudo, passwd, chown, chmod, chattr, kill, killall, pkill, taskkill, crontab, at, systemctl, service.",
                "Use 'working_dir' for operations within specific directories (relative to project root).",
                "Ensure commands are non-interactive and complete within the 'timeout' period.",
                "When debugging failures: Read stderr output carefully for specific error messages and missing dependencies.",
                "For test failures: Look at the full error output, not just exit codes - often shows import errors, missing files, or syntax issues.",
                "For Python projects: Install requirements before running tests. Create __init__.py files to make directories into packages.",
                "For ModuleNotFoundError: Check if the module exists as a file/directory and create __init__.py if needed to make it importable.",
            ],
        )
        # Coordinate with file tool sandbox
        self.default_working_dir = Path(default_working_dir).resolve()
        self.default_working_dir.mkdir(parents=True, exist_ok=True)
        # Security: blocked dangerous commands
        self._blocked_commands = {
            "rm",
            "rmdir",
            "del",
            "format",
            "fdisk",
            "mkfs",
            "dd",
            "shutdown",
            "reboot",
            "halt",
            "poweroff",
            "init",
            "su",
            "sudo",
            "passwd",
            "chown",
            "chmod",
            "chattr",
            "kill",
            "killall",
            "pkill",
            "taskkill",
            "crontab",
            "at",
            "systemctl",
            "service",
        }

    async def run(
        self,
        command: str,
        timeout: int = 30,
        working_dir: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        """Execute shell command with safety checks.

        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds (default: 30, max: 300)
            working_dir: Optional working directory (must be safe)
            env: Optional environment variables to add

        Returns:
            Command execution results including stdout, stderr, and exit code
        """
        # Schema validation handles required params
        # Security checks

        # Limit timeout
        timeout = min(max(timeout, 1), 300)  # 1-300 seconds

        # Parse command to check for blocked commands
        try:
            cmd_parts = shlex.split(command)
            if not cmd_parts:
                return Result.fail("Invalid command format")

            base_cmd = Path(cmd_parts[0]).name.lower()
            if base_cmd in self._blocked_commands:
                return Result.fail(f"Command '{base_cmd}' is blocked for security")

        except ValueError as e:
            return Result.fail(f"Invalid command syntax: {str(e)}")

        # Validate working directory
        if working_dir:
            try:
                work_path = Path(working_dir).resolve()
                if not work_path.exists():
                    return Result.fail(f"Working directory does not exist: {working_dir}")
                if not work_path.is_dir():
                    return Result.fail(f"Working directory is not a directory: {working_dir}")
                # Basic sandbox: no system directories
                forbidden_paths = {
                    "/",
                    "/bin",
                    "/sbin",
                    "/usr",
                    "/etc",
                    "/sys",
                    "/proc",
                    "/dev",
                }
                work_path_str = str(work_path)
                # Check if it's a forbidden system directory (but not subdirectories of allowed paths)
                if work_path_str in forbidden_paths or any(
                    work_path_str.startswith(p + "/") for p in forbidden_paths
                ):
                    return Result.fail(f"Access to system directory forbidden: {working_dir}")
            except Exception as e:
                logger.error(f"Error validating working directory {working_dir}: {e}")
                return Result.fail(f"Invalid working directory: {working_dir}")

        # Prepare environment
        process_env = os.environ.copy()
        if env:
            # Sanitize environment variables
            for key, value in env.items():
                if isinstance(key, str) and isinstance(value, str):
                    process_env[key] = value

        # Execute command with coordinated working directory
        actual_working_dir = working_dir or str(self.default_working_dir)
        try:
            process = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=actual_working_dir,
                env=process_env,
                limit=1024 * 1024,  # 1MB output limit
            )

            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
                exit_code = process.returncode

            except asyncio.TimeoutError:
                # Kill the process on timeout
                try:
                    process.kill()
                    await process.wait()
                except (ProcessLookupError, OSError) as e:
                    logger.warning(f"Failed to kill process after timeout: {e}")
                return Result.fail(f"Command timed out after {timeout} seconds")

            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

            # Truncate very long output
            max_output = 10000  # 10KB per stream
            if len(stdout_text) > max_output:
                stdout_text = stdout_text[:max_output] + "\n... (output truncated)"
            if len(stderr_text) > max_output:
                stderr_text = stderr_text[:max_output] + "\n... (output truncated)"

            return Result.ok(
                {
                    "exit_code": exit_code,
                    "success": exit_code == 0,
                    "stdout": stdout_text,
                    "stderr": stderr_text,
                    "command": command,
                    "working_dir": actual_working_dir,
                    "timeout": timeout,
                }
            )

        except FileNotFoundError as e:
            logger.error(f"Command not found: {e}")
            return Result.fail("Command not found")
        except PermissionError as e:
            logger.error(f"Permission denied for command: {e}")
            return Result.fail("Permission denied")
        except Exception as e:
            logger.error(f"Command execution failed: {e}")
            return Result.fail(f"Command execution failed: {str(e)}")

    def format_human(
        self, params: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format shell execution for display."""
        from cogency.utils import truncate

        cmd = params.get("command", "")
        param_str = f"({truncate(cmd, 35)})" if cmd else ""

        if results is None:
            return param_str, ""

        # Enhanced result formatting
        if results.failure:
            result_str = results.error
        else:
            data = results.data
            exit_code = data.get("exit_code", 0)
            stdout = data.get("stdout", "").strip()

            if exit_code == 0:
                # Show meaningful success messages
                if "pip install" in cmd and "Successfully installed" in stdout:
                    result_str = "Packages installed successfully"
                elif "pytest" in cmd and "passed" in stdout:
                    # Extract test results from pytest output
                    if "failed" in stdout:
                        result_str = "Tests completed (some failures)"
                    else:
                        result_str = "All tests passed"
                elif "python" in cmd and stdout:
                    result_str = f"Executed: {stdout[:50]}..." if len(stdout) > 50 else stdout
                elif stdout:
                    result_str = f"{stdout[:50]}..." if len(stdout) > 50 else stdout
                else:
                    result_str = "Command completed successfully"
            else:
                stderr = data.get("stderr", "").strip()
                if stderr:
                    result_str = (
                        f"Exit code: {exit_code} - {stderr[:100]}..."
                        if len(stderr) > 100
                        else f"Exit code: {exit_code} - {stderr}"
                    )
                else:
                    result_str = f"Exit code: {exit_code}"

        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format shell execution results for agent action history."""
        if not result_data:
            return "No result"

        # Use command for consistent fingerprinting, not dynamic output
        command = result_data.get("command", "")
        success = result_data.get("success", False)

        if success:
            return f"✓ {command}"
        else:
            exit_code = result_data.get("exit_code", "unknown")
            return f"✗ {command} (exit {exit_code})"
