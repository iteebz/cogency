import glob
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

from ..core.protocols import ToolParam, ToolResult
from ..core.security import safe_execute, sanitize_shell_input
from ..core.tool import tool


@dataclass
class ShellParams:
    command: Annotated[str, ToolParam(description="Shell command to execute")]
    cwd: Annotated[
        str | None,
        ToolParam(description="Working directory for command (relative to project root)"),
    ] = None


@tool("Run shell command (30s timeout). Each call starts in project root.")
@safe_execute
async def Shell(
    params: ShellParams,
    timeout: int = 30,
    sandbox_dir: str = ".cogency/sandbox",
    access: str = "sandbox",
    **kwargs,
) -> ToolResult:
    if not params.command or not params.command.strip():
        return ToolResult(outcome="Command cannot be empty", error=True)

    sanitized = sanitize_shell_input(params.command.strip())
    parts = shlex.split(sanitized)

    if not parts:
        return ToolResult(outcome="Empty command after parsing", error=True)

    if params.cwd:
        working_path = Path(params.cwd)
        if not working_path.is_absolute():
            base = Path(sandbox_dir) if access == "sandbox" else Path.cwd()
            working_path = (base / working_path).resolve()
    elif access == "sandbox":
        working_path = Path(sandbox_dir)
    else:
        working_path = Path.cwd()

    working_path.mkdir(parents=True, exist_ok=True)

    expanded_parts = [parts[0]]
    for arg in parts[1:]:
        if any(char in arg for char in "*?["):
            matches = glob.glob(arg, root_dir=str(working_path))
            if matches:
                expanded_parts.extend(matches)
                continue
        expanded_parts.append(arg)

    try:
        result = subprocess.run(
            expanded_parts,
            cwd=str(working_path),
            capture_output=True,
            text=True,
            timeout=timeout,
        )

        if result.returncode == 0:
            content_parts = []

            if result.stdout.strip():
                content_parts.append(result.stdout.strip())

            if result.stderr.strip():
                content_parts.append(f"Warnings:\n{result.stderr.strip()}")

            content = "\n".join(content_parts) if content_parts else ""
            outcome = "Success"

            return ToolResult(outcome=outcome, content=content)
        error_output = result.stderr.strip() or "Command failed"
        return ToolResult(
            outcome=f"Command failed (exit {result.returncode}): {error_output}", error=True
        )

    except subprocess.TimeoutExpired:
        return ToolResult(outcome=f"Command timed out after {timeout} seconds", error=True)
    except FileNotFoundError:
        return ToolResult(outcome=f"Command not found: {parts[0]}", error=True)
