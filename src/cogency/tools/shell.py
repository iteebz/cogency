import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated, Any

from cogency.core.config import Access
from cogency.core.errors import ToolError
from cogency.core.protocols import ToolParam, ToolResult
from cogency.core.security import resolve_file, safe_execute, sanitize_shell_input
from cogency.core.tool import tool


@dataclass
class ShellParams:
    command: Annotated[str, ToolParam(description="Shell command to execute")]
    cwd: Annotated[
        str | None,
        ToolParam(description="Working directory for command (relative to project root)"),
    ] = None


def _resolve_working_dir(cwd: str | None, access: Access, sandbox_dir: str) -> Path:
    if cwd:
        working_path = resolve_file(cwd, access, sandbox_dir)
    elif access == "sandbox":
        working_path = Path(sandbox_dir).resolve()
    else:
        working_path = Path.cwd().resolve()

    working_path.mkdir(parents=True, exist_ok=True)
    return working_path


def _format_result(result: subprocess.CompletedProcess[str]) -> ToolResult:
    if result.returncode != 0:
        error_output = result.stderr.strip() or "Command failed"
        return ToolResult(
            outcome=f"Command failed (exit {result.returncode}): {error_output}", error=True
        )

    content_parts: list[str] = []
    if result.stdout.strip():
        content_parts.append(result.stdout.strip())
    if result.stderr.strip():
        content_parts.append(f"Warnings:\n{result.stderr.strip()}")

    return ToolResult(outcome="Success", content="\n".join(content_parts) if content_parts else "")


@tool("Run shell command (30s timeout). Each call starts in project root.")
@safe_execute
async def shell(
    params: ShellParams,
    timeout: int = 30,
    sandbox_dir: str = ".cogency/sandbox",
    access: Access = "sandbox",
    **kwargs: Any,
) -> ToolResult:
    if not params.command or not params.command.strip():
        return ToolResult(outcome="Command cannot be empty", error=True)

    sanitized = sanitize_shell_input(params.command.strip())
    parts = shlex.split(sanitized)

    if not parts:
        return ToolResult(outcome="Empty command after parsing", error=True)

    try:
        working_path = _resolve_working_dir(params.cwd, access, sandbox_dir)
    except ToolError as e:
        return ToolResult(outcome=str(e), error=True)

    try:
        result = subprocess.run(
            parts,
            cwd=str(working_path),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return _format_result(result)

    except subprocess.TimeoutExpired:
        return ToolResult(outcome=f"Command timed out after {timeout} seconds", error=True)
    except FileNotFoundError:
        return ToolResult(outcome=f"Command not found: {parts[0]}", error=True)
