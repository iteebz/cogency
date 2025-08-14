"""Tool security - boundary enforcement for tool operations.

Security validation at tool boundaries to prevent dangerous operations.
Tools self-secure rather than relying on external validation.
"""

import re
from enum import Enum
from typing import Any


class SecurityThreat(Enum):
    """Security threat classification."""

    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    INFORMATION_LEAKAGE = "information_leakage"


class SecurityAction(Enum):
    """Security response actions."""

    ALLOW = "allow"
    BLOCK = "block"
    REDACT = "redact"


class SecurityResult:
    """Security assessment result."""

    def __init__(self, action: SecurityAction, threat: SecurityThreat = None, message: str = ""):
        self.action = action
        self.threat = threat
        self.message = message
        self.safe = action == SecurityAction.ALLOW

    def __bool__(self):
        return self.safe


def secure_tool(content: str, context: dict[str, Any] = None) -> SecurityResult:
    """Tool boundary security enforcement.

    Validates tool inputs/outputs for dangerous patterns and content.
    Applied at tool boundaries to enforce operational security.

    Args:
        content: Content to validate for security threats
        context: Optional context for validation decisions

    Returns:
        SecurityResult indicating action to take
    """
    if not content:
        return SecurityResult(SecurityAction.ALLOW)

    content_lower = content.lower()

    # Command injection patterns for tools
    if any(pattern in content_lower for pattern in ["rm -rf", "format c:", "shutdown", "del /s"]):
        return SecurityResult(
            SecurityAction.BLOCK,
            SecurityThreat.COMMAND_INJECTION,
            "Dangerous system command detected",
        )

    # Path traversal patterns for file operations
    if any(pattern in content_lower for pattern in ["../../..", "..\\..\\..", "%2e%2e%2f"]):
        return SecurityResult(
            SecurityAction.BLOCK, SecurityThreat.PATH_TRAVERSAL, "Path traversal attempt detected"
        )

    return SecurityResult(SecurityAction.ALLOW)


def secure_response(text: str) -> str:
    """Make response secure by redacting secrets.

    Args:
        text: Response text to secure

    Returns:
        Text with secrets redacted
    """
    return redact_secrets(text)


def redact_secrets(text: str) -> str:
    """Apply regex redaction for common secrets.

    Args:
        text: Text to scan and redact

    Returns:
        Text with secrets replaced with [REDACTED]
    """
    # API keys and tokens (handles sk-proj- and sk- variants)
    text = re.sub(r"sk-[a-zA-Z0-9_-]{20,}", "[REDACTED]", text)
    return re.sub(r"AKIA[a-zA-Z0-9]{16}", "[REDACTED]", text)
