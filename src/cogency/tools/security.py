"""Tool security utilities.

Input validation, path safety, and secret redaction for tools.
"""

import re
from pathlib import Path


def validate_input(content: str) -> bool:
    """Basic input validation for tool operations."""
    if not content:
        return True

    content_lower = content.lower()
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
    """Resolve path safely within base directory."""
    if not rel_path:
        raise ValueError("Path cannot be empty")

    resolved = (base_dir / rel_path).resolve()
    if not str(resolved).startswith(str(base_dir.resolve())):
        raise ValueError(f"Path escapes base directory: {rel_path}")

    return resolved


def redact_secrets(text: str) -> str:
    """Redact common secrets from text."""
    text = re.sub(r"sk-[a-zA-Z0-9_-]{6,}", "[REDACTED]", text)
    return re.sub(r"AKIA[a-zA-Z0-9]{12,}", "[REDACTED]", text)
