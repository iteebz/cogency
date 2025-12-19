"""Defense in depth: LLM instruction (probabilistic) + pattern validation + sandbox (deterministic)."""

import shlex
import signal
import types
from collections.abc import Awaitable, Callable
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import TYPE_CHECKING, Any, TypeVar

from .errors import ToolError
from .protocols import ToolResult

if TYPE_CHECKING:
    from .config import Access

F = TypeVar("F", bound=Callable[..., Awaitable[ToolResult]])


def _has_unquoted(command: str, targets: set[str]) -> str | None:
    single = double = False
    escaped = False

    for ch in command:
        if escaped:
            escaped = False
            continue

        if ch == "\\":
            # Outside single quotes, backslash escapes the next character.
            if not single:
                escaped = True
            continue

        if ch == "'" and not double:
            single = not single
            continue

        if ch == '"' and not single:
            double = not double
            continue

        if ch in targets and not single and not double:
            return ch

    # Unbalanced quotes - leave detection to shlex which will error.
    return None


def _has_dollar_outside_single_quotes(command: str) -> str | None:
    single = double = False
    escaped = False

    for ch in command:
        if escaped:
            escaped = False
            continue

        if ch == "\\":
            if not single:
                escaped = True
            continue

        if ch == "'" and not double:
            single = not single
            continue

        if ch == '"' and not single:
            double = not double
            continue

        if ch == "$" and not single:
            return ch

    return None


def sanitize_shell_input(command: str) -> str:
    if not command or not command.strip():
        raise ToolError("Command cannot be empty", validation_failed=True)

    command = command.strip()

    # Characters that must never appear, even inside quotes.
    hard_blocked = {"\n", "\r", "\x00"}
    if any(char in command for char in hard_blocked):
        raise ToolError("Invalid shell command syntax", validation_failed=True)

    # Reject metacharacters if they appear outside of quotes.
    # - `;`, `&`, `|`, `` ` ``, `<`, `>` perform command chaining/redirection.
    # - `；`, `｜` are full-width variants.
    # - `$` enables expansion unless wrapped in single quotes.
    if char := _has_unquoted(command, {";", "&", "|", "`", "<", ">", "；", "｜"}):
        if "&&" in command:
            raise ToolError(
                "Chained commands not supported. Each shell call is independent - use cwd argument to run in different directories.",
                validation_failed=True,
            )
        raise ToolError(
            f"Invalid shell command syntax: character '{char}' is not allowed",
            validation_failed=True,
        )

    # Allow `$` inside single quotes (no expansion), block otherwise.
    if char := _has_dollar_outside_single_quotes(command):
        raise ToolError(
            f"Invalid shell command syntax: character '{char}' is not allowed",
            validation_failed=True,
        )

    # Validate shell syntax
    try:
        tokens = shlex.split(command)
        if not tokens:
            raise ToolError("Command cannot be empty", validation_failed=True)
        return shlex.join(tokens)
    except ValueError as e:
        raise ToolError(f"Invalid shell command syntax: {e}", validation_failed=True) from None


def validate_path(file_path: str, base_dir: Path | None = None) -> Path:
    if not file_path or not file_path.strip():
        raise ToolError("Path cannot be empty", validation_failed=True)

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
        raise ToolError("Invalid path", validation_failed=True)

    if base_dir:
        # Sandbox mode: relative paths only
        if Path(file_path).is_absolute():
            raise ToolError("Path outside sandbox", validation_failed=True)

        try:
            return (base_dir / file_path).resolve()
        except (OSError, ValueError):
            raise ToolError("Invalid path", validation_failed=True) from None
    else:
        # System mode: allow absolute paths
        try:
            return Path(file_path).resolve()
        except (OSError, ValueError):
            raise ToolError("Invalid path", validation_failed=True) from None


def resolve_file(file: str, access: "Access", sandbox_dir: str = ".cogency/sandbox") -> Path:
    if access == "sandbox":
        parts = Path(file).parts
        if parts and parts[0] == "sandbox":
            file = str(Path(*parts[1:])) if len(parts) > 1 else "."
        base = Path(sandbox_dir)
        base.mkdir(parents=True, exist_ok=True)
        return validate_path(file, base)
    if access == "project":
        return validate_path(file, Path.cwd())
    if access == "system":
        return validate_path(file)
    raise ToolError(f"Invalid access level: {access}", validation_failed=True)


@contextmanager
def timeout_context(seconds: int):
    def timeout_handler(signum: int, frame: types.FrameType | None) -> None:
        raise TimeoutError(f"Operation timed out after {seconds} seconds")

    old_handler = None
    try:
        old_handler = signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(seconds)
        yield
    except AttributeError:
        yield
    finally:
        try:
            signal.alarm(0)
            if old_handler is not None:
                signal.signal(signal.SIGALRM, old_handler)
        except AttributeError:
            pass


def safe_execute(func: F) -> F:
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> ToolResult:
        try:
            return await func(*args, **kwargs)
        except ToolError as e:
            if e.validation_failed:
                return ToolResult(outcome=str(e), error=True)
            raise

    return wrapper  # type: ignore[return-value]  # decorator variance limitation
