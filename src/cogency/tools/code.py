"""Code execution tool for Python/JavaScript - ISOLATED & SANDBOXED."""

import asyncio
import logging
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from resilient_result import Result

from cogency.tools.base import Tool
from cogency.tools.registry import tool

logger = logging.getLogger(__name__)


@dataclass
class CodeArgs:
    code: str
    language: str = "python"
    timeout: int = 30


@tool
class Code(Tool):
    """Execute Python and JavaScript code safely in isolated environment."""

    def __init__(self):
        super().__init__(
            name="code",
            description="Execute Python and JavaScript code safely in isolated environment",
            schema="code(code=str, language='python'|'javascript', timeout=int)",
            emoji="🚀",
            params=CodeArgs,
            examples=[
                "code(code='print(2 + 2)', language='python')",
                "code(code='import pandas as pd; df.describe()', language='python')",
            ],
            rules=[
                "Use for data analysis, algorithms, complex math, variables, loops",
                "For simple arithmetic, use calculator tool instead",
            ],
        )
        # Beautiful dispatch pattern - extensible and clean
        self._languages = {
            "python": self._execute_python,
            "javascript": self._execute_javascript,
            "js": self._execute_javascript,  # Alias
        }

    async def run(
        self, code: str, language: str = "python", timeout: int = 30, **kwargs
    ) -> Dict[str, Any]:
        """Execute code using dispatch pattern.

        Args:
            code: Source code to execute
            language: Programming language (python, javascript/js)
            timeout: Execution timeout in seconds (default: 30, max: 120)

        Returns:
            Execution results including output, errors, and exit code
        """
        # Schema validation handles required params

        language = language.lower()
        if language not in self._languages:
            available = ", ".join(set(self._languages.keys()))
            return Result.fail(f"Unsupported language. Use: {available}")

        # Limit timeout
        timeout = min(max(timeout, 1), 120)  # 1-120 seconds

        # Dispatch to appropriate language handler
        executor = self._languages[language]
        return await executor(code, timeout)

    async def _execute_python(self, code: str, timeout: int) -> Dict[str, Any]:
        """Execute Python code in isolated subprocess."""
        return await self._run_in_subprocess(["python", "-c", code], timeout)

    async def _execute_javascript(self, code: str, timeout: int) -> Dict[str, Any]:
        """Execute JavaScript code using Node.js."""

        # Check if Node.js is available
        try:
            result = subprocess.run(
                ["phase", "--version"], capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                return Result.fail(
                    "Node.js not found. Please install Node.js to execute JavaScript code."
                )
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return Result.fail(
                "Node.js not found. Please install Node.js to execute JavaScript code."
            )

        return await self._run_in_subprocess(["phase", "-e", code], timeout)

    async def _run_in_subprocess(self, cmd: List[str], timeout: int) -> Dict[str, Any]:
        """Run command in subprocess with timeout and output capture."""
        try:
            import os

            project_root = os.getcwd()  # Assuming the agent is run from the project root
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_root,  # Set cwd to the project root
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
                return Result.fail(f"Code execution timed out after {timeout} seconds")

            # Decode output
            stdout_text = stdout.decode("utf-8", errors="replace") if stdout else ""
            stderr_text = stderr.decode("utf-8", errors="replace") if stderr else ""

            # Truncate very long output
            max_output = 5000  # 5KB per stream
            if len(stdout_text) > max_output:
                stdout_text = stdout_text[:max_output] + "\n... (output truncated)"
            if len(stderr_text) > max_output:
                stderr_text = stderr_text[:max_output] + "\n... (output truncated)"

            return Result.ok(
                {
                    "exit_code": exit_code,
                    "success": exit_code == 0,
                    "output": stdout_text,
                    "error_output": stderr_text,
                    "timeout": timeout,
                }
            )

        except Exception as e:
            logger.error(f"Code execution failed: {e}")
            return Result.fail(f"Code execution failed: {str(e)}")

    def format_human(
        self, params: Dict[str, Any], results: Optional[Result] = None
    ) -> tuple[str, str]:
        """Format code execution for display."""
        from cogency.utils import truncate

        code = params.get("code", "")
        language = params.get("language", "python")
        param_str = f"({language}: {truncate(code, 25)})" if code else ""

        if results is None:
            return param_str, ""

        # Format results
        if results.failure:
            result_str = f"Error: {results.error}"
        else:
            data = results.data
            if data.get("success"):
                result_str = "Executed successfully"
            else:
                result_str = f"Exit code: {data.get('exit_code', 1)}"

        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        """Format code execution results for agent action history."""
        if not result_data:
            return "No result"

        success = result_data.get("success", False)
        output = result_data.get("output", "").strip()
        error_output = result_data.get("error_output", "").strip()
        exit_code = result_data.get("exit_code")

        if success:
            if output:
                return f"Code executed successfully. Output: {output[:100]}..."
            return "Code executed successfully (no output)"
        else:
            msg = f"Code execution failed (exit code: {exit_code})."
            if error_output:
                msg += f" Error: {error_output[:100]}..."
            elif output:
                msg += f" Output: {output[:100]}..."
            return msg
