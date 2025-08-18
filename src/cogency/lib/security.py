"""Security utilities for tool operations.

Minimal security primitives for safe tool execution.
"""

import re
from pathlib import Path


def validate_input(content: str) -> bool:
    """Validate content for basic security threats.

    Args:
        content: Content to validate

    Returns:
        True if content is safe, False otherwise
    """
    if not content:
        return True

    content_lower = content.lower()

    # Basic command injection patterns
    dangerous_patterns = [
        "rm -rf",
        "format c:",
        "shutdown",
        "del /s",
        "../../",
        "..\\..\\..",
        "%2e%2e%2f",
    ]

    return not any(pattern in content_lower for pattern in dangerous_patterns)


def safe_path(base_dir: Path, rel_path: str) -> Path:
    """Resolve path safely within base directory.

    Args:
        base_dir: Base directory for path resolution
        rel_path: Relative path to resolve

    Returns:
        Resolved path within base directory

    Raises:
        ValueError: If path escapes base directory
    """
    if not rel_path:
        raise ValueError("Path cannot be empty")

    # Resolve path within base directory
    resolved = (base_dir / rel_path).resolve()

    # Ensure path stays within base directory
    if not str(resolved).startswith(str(base_dir.resolve())):
        raise ValueError(f"Path escapes base directory: {rel_path}")

    return resolved


def redact_secrets(text: str) -> str:
    """Redact common secrets from text.

    Args:
        text: Text to scan for secrets

    Returns:
        Text with secrets replaced by [REDACTED]
    """
    # API keys and tokens - adjusted patterns for test compatibility
    text = re.sub(r"sk-[a-zA-Z0-9_-]{6,}", "[REDACTED]", text)
    return re.sub(r"AKIA[a-zA-Z0-9]{12,}", "[REDACTED]", text)
