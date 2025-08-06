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

    def __init__(self, default_working_dir: str = None):
        from ..config import PathsConfig

        if default_working_dir is None:
            default_working_dir = PathsConfig().sandbox
        super().__init__(
            name="shell",
            description="Run shell commands and scripts - for executing files, running programs, terminal operations",
            schema="shell(command: str, timeout: int = 30, working_dir: str = None, env: dict = None)",
            emoji="💻",
            args=ShellArgs,
            examples=[
                '{"name": "shell", "args": {"command": "ls -la"}}',
                '{"name": "shell", "args": {"command": "pwd"}}',
                '{"name": "shell", "args": {"command": "echo \\"Hello World\\""}}',
                '{"name": "shell", "args": {"command": "python --version"}}',
                '{"name": "shell", "args": {"command": "git status", "working_dir": "/path/to/repo"}}',
                '{"name": "shell", "args": {"command": "python -m pip install -r requirements.txt"}}',
            ],
            rules=[
                "Prefer 'python -m <module>' for executing Python modules (e.g., 'python -m pip', 'python -m pytest').",
                "For file search: Use 'rg pattern' (ripgrep) over grep for faster, better formatted results.",
                "Avoid using commands that modify system state or delete files (e.g., 'rm', 'sudo').",
                "Blocked commands include: rm, rmdir, del, sudo, su, shutdown, reboot, kill, killall.",
                "Use 'working_dir' for operations within specific directories (relative to project root).",
                "Ensure commands are non-interactive and complete within the 'timeout' period.",
                "When debugging failures: Read stderr output carefully for specific error messages and missing dependencies.",
                "For test failures: Look at the full error output, not just exit codes - often shows import errors, missing files, or syntax issues.",
                "For Python projects: Install requirements before running tests. Create __init__.py files to make directories into packages.",
                "For ModuleNotFoundError: Check if the module exists as a file/directory and create __init__.py if needed to make it importable.",
            ],
        )
        # Use base class formatting with templates
        self.arg_key = "command"
        self.human_template = "Exit code: {exit_code}"
        self.agent_template = "{command} → {exit_code}"

        # Coordinate with file tool sandbox
        self.default_working_dir = Path(default_working_dir).resolve()
        self.default_working_dir.mkdir(parents=True, exist_ok=True)

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
        # Schema validation handles required args
        # Security checks

        # Limit timeout
        timeout = min(max(timeout, 1), 300)  # 1-300 seconds

        # Security: validate command using centralized patterns
        from cogency.security import secure_tool

        security_result = secure_tool(command)
        if not security_result.safe:
            return Result.fail(f"Security violation: {security_result.message}")

        # Parse command for additional validation
        try:
            cmd_parts = shlex.split(command)
            if not cmd_parts:
                return Result.fail("Invalid command format")
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
                stdout_text = stdout_text[:max_output] + "\n... (output _truncated)"
            if len(stderr_text) > max_output:
                stderr_text = stderr_text[:max_output] + "\n... (output _truncated)"

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
