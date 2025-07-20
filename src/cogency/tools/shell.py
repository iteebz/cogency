"""Shell tool for safe system command execution - SANDBOXED & TIMEOUT PROTECTED."""
import asyncio
import logging
import shlex
import subprocess
from typing import Any, Dict, List, Optional
import os
import tempfile
from pathlib import Path

from .base import BaseTool
from .registry import tool

logger = logging.getLogger(__name__)


@tool
class Shell(BaseTool):
    """Execute system commands safely with timeout and basic sandboxing."""

    def __init__(self, default_working_dir: str = ".cogency/sandbox"):
        super().__init__(
            name="shell",
            description="Run shell commands and scripts - for executing files, running programs, terminal operations",
            emoji="💻"
        )
        # Coordinate with file tool sandbox
        self.default_working_dir = Path(default_working_dir).resolve()
        self.default_working_dir.mkdir(parents=True, exist_ok=True)
        # Security: blocked dangerous commands
        self._blocked_commands = {
            "rm", "rmdir", "del", "format", "fdisk", "mkfs", "dd", 
            "shutdown", "reboot", "halt", "poweroff", "init",
            "su", "sudo", "passwd", "chown", "chmod", "chattr",
            "kill", "killall", "pkill", "taskkill",
            "crontab", "at", "systemctl", "service"
        }

    async def run(self, command: str, timeout: int = 30, working_dir: Optional[str] = None,
                  env: Optional[Dict[str, str]] = None, **kwargs) -> Dict[str, Any]:
        """Execute shell command with safety checks.
        
        Args:
            command: Shell command to execute
            timeout: Command timeout in seconds (default: 30, max: 300)
            working_dir: Optional working directory (must be safe)
            env: Optional environment variables to add
            
        Returns:
            Command execution results including stdout, stderr, and exit code
        """
        # Security checks
        if not command or not command.strip():
            return {"error": "Command cannot be empty"}
        
        # Limit timeout
        timeout = min(max(timeout, 1), 300)  # 1-300 seconds
        
        # Parse command to check for blocked commands
        try:
            cmd_parts = shlex.split(command)
            if not cmd_parts:
                return {"error": "Invalid command format"}
            
            base_cmd = Path(cmd_parts[0]).name.lower()
            if base_cmd in self._blocked_commands:
                return {"error": f"Command '{base_cmd}' is blocked for security"}
                
        except ValueError as e:
            return {"error": f"Invalid command syntax: {str(e)}"}
        
        # Validate working directory
        if working_dir:
            try:
                work_path = Path(working_dir).resolve()
                if not work_path.exists():
                    return {"error": f"Working directory does not exist: {working_dir}"}
                if not work_path.is_dir():
                    return {"error": f"Working directory is not a directory: {working_dir}"}
                # Basic sandbox: no system directories
                forbidden_paths = {"/", "/bin", "/sbin", "/usr", "/etc", "/sys", "/proc", "/dev"}
                work_path_str = str(work_path)
                # Check if it's a forbidden system directory (but not subdirectories of allowed paths)
                if work_path_str in forbidden_paths or any(work_path_str.startswith(p + "/") for p in forbidden_paths):
                    return {"error": f"Access to system directory forbidden: {working_dir}"}
            except Exception:
                return {"error": f"Invalid working directory: {working_dir}"}
        
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
                limit=1024 * 1024  # 1MB output limit
            )
            
            # Wait for completion with timeout
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=timeout
                )
                exit_code = process.returncode
                
            except asyncio.TimeoutError:
                # Kill the process on timeout
                try:
                    process.kill()
                    await process.wait()
                except:
                    pass
                return {"error": f"Command timed out after {timeout} seconds"}
            
            # Decode output
            stdout_text = stdout.decode('utf-8', errors='replace') if stdout else ""
            stderr_text = stderr.decode('utf-8', errors='replace') if stderr else ""
            
            # Truncate very long output
            max_output = 10000  # 10KB per stream
            if len(stdout_text) > max_output:
                stdout_text = stdout_text[:max_output] + "\n... (output truncated)"
            if len(stderr_text) > max_output:
                stderr_text = stderr_text[:max_output] + "\n... (output truncated)"
            
            return {
                "exit_code": exit_code,
                "success": exit_code == 0,
                "stdout": stdout_text,
                "stderr": stderr_text,
                "command": command,
                "working_dir": actual_working_dir,
                "timeout": timeout
            }
            
        except FileNotFoundError:
            return {"error": "Command not found"}
        except PermissionError:
            return {"error": "Permission denied"}
        except Exception as e:
            return {"error": f"Command execution failed: {str(e)}"}

    def get_schema(self) -> str:
        """Return the tool call schema."""
        return (
            "shell(command='string', timeout=int, working_dir='string', env=dict) - "
            "Examples: shell(command='ls -la'), shell(command='pwd'), "
            "shell(command='echo hello world', timeout=10)"
        )

    def get_usage_examples(self) -> List[str]:
        """Return example usage patterns."""
        return [
            "shell(command='ls -la')",
            "shell(command='pwd')",
            "shell(command='echo \"Hello World\"')",
            "shell(command='python --version')",
            "shell(command='git status', working_dir='/path/to/repo')"
        ]
    
    def format_params(self, params: Dict[str, Any]) -> str:
        """Format parameters for display."""
        from cogency.messaging import _truncate
        cmd = params.get("command", "")
        return f"({_truncate(cmd, 35)})" if cmd else ""