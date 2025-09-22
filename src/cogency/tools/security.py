"""Tool security with semantic and pattern-based validation.

Security architecture combines two approaches:
1. Pattern-based validation - catches common attacks (path traversal, shell injection)
2. Semantic security - LLM reasoning detects sophisticated/novel attacks

Pattern validation handles known attack vectors efficiently.
Semantic security (system prompt) provides adaptive defense against novel attacks.
"""

import shlex
import signal
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING

from ..core.protocols import ToolResult

if TYPE_CHECKING:
    from ..core.config import Access


def sanitize_shell_input(command: str) -> str:
    """Validate shell input and reject dangerous patterns. [SEC-002]"""
    if not command or not command.strip():
        raise ValueError("Command cannot be empty")

    command = command.strip()

    # Shell metacharacters that enable command injection
    dangerous_chars = [
        ";",
        "&",
        "|",
        "`",
        "$",  # Prevents variable expansion attacks: $HOME, $(cmd), ${IFS}
        ">",
        "<",
        "\n",
        "\r",
        "\x00",
        "；",
        "｜",
    ]
    for char in dangerous_chars:
        if char in command:
            raise ValueError("Invalid shell command syntax")

    # Validate shell syntax
    try:
        tokens = shlex.split(command)
        if not tokens:
            raise ValueError("Command cannot be empty")
        return shlex.join(tokens)
    except ValueError as e:
        raise ValueError(f"Invalid shell command syntax: {e}") from None


def validate_path(file_path: str, base_dir: Path = None) -> Path:
    """Prevent common path attacks. Semantic security handles sophisticated ones. [SEC-004]

    Blocks:
    - Path traversal (../)
    - System directories (/etc, /bin, etc.)
    - Null bytes and empty paths
    - Absolute paths in sandbox mode

    Does not block every exotic Unicode/encoding variant - relies on
    semantic security (LLM reasoning) for sophisticated attacks. [SEC-001]
    """
    if not file_path or not file_path.strip():
        raise ValueError("Path cannot be empty")

    file_path = file_path.strip()

    # Block dangerous patterns in one check [SEC-002, SEC-004]
    dangerous_patterns = [
        "\\x00",
        "..",
        "\\",
        "/etc/",
        "/bin/",
        "/sbin/",
        "/usr/bin/",
        "/System/",
        "C:\\",
    ]
    if any(pattern in file_path for pattern in dangerous_patterns):
        raise ValueError("Invalid path")

    if base_dir:
        # Sandbox mode: relative paths only
        if Path(file_path).is_absolute():
            raise ValueError("Path outside sandbox")

        try:
            return (base_dir / file_path).resolve()
        except (OSError, ValueError):
            raise ValueError("Invalid path") from None
    else:
        # System mode: allow absolute paths
        try:
            return Path(file_path).resolve()
        except (OSError, ValueError):
            raise ValueError("Invalid path") from None


def resolve_file(file: str, access: "Access") -> Path:
    """Resolve file path based on access level."""
    from ..lib.paths import Paths

    if access == "sandbox":
        return validate_path(file, Paths.sandbox())
    if access == "project":
        return validate_path(file, Path.cwd())
    if access == "system":
        return validate_path(file)
    raise ValueError(f"Invalid access level: {access}")


@contextmanager
def timeout_context(seconds: int):
    """Context manager for operation timeouts."""

    def timeout_handler(signum, frame):
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    # Set up signal handler (Unix only)
    try:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        yield
    except AttributeError:
        # Windows - no signal.SIGALRM, just yield without timeout
        yield
    finally:
        try:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)
        except AttributeError:
            pass


def safe_execute(func):
    """Decorator for safe tool execution - handles input validation errors only."""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ValueError as e:
            # Input validation error - return as tool result
            return ToolResult(outcome=f"Invalid input: {str(e)}")
        # Let system errors (OSError, PermissionError, etc) bubble up
        # These should halt processing, not become tool results

    return wrapper
