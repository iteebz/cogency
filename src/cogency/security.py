"""Semantic Security - Minimal threat detection via LLM inference."""

from enum import Enum
from typing import Any, Dict


class SecurityThreat(Enum):
    """Security threat classification."""

    PROMPT_INJECTION = "prompt_injection"
    COMMAND_INJECTION = "command_injection"
    PATH_TRAVERSAL = "path_traversal"
    INFORMATION_LEAKAGE = "information_leakage"
    RESPONSE_HIJACKING = "response_hijacking"


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


async def assess(text: str, context: Dict[str, Any] = None) -> SecurityResult:
    """Semantic security assessment - the only way to validate anything.

    Uses LLM reasoning to understand intent, with minimal threat pattern fallbacks.
    Security that fades into the background.
    """
    from cogency.events import emit

    context = context or {}

    # Emit start of assessment
    emit("security", level="debug", operation="assess", status="checking", text_length=len(text))

    try:
        # Threat patterns - immediate protection that also trains the LLM
        threat_result = _threat_patterns(
            text, context
        )  # SEC-002, SEC-004: Command injection & path traversal
        if not threat_result.safe:
            emit(
                "security",
                operation="assess",
                status="blocked",
                threat=threat_result.threat.value,
                reason=threat_result.message,
            )
            return threat_result

        # Semantic assessment via LLM (when available)
        if "security_assessment" in context:
            result = _semantic_assessment(text, context)
            emit(
                "security",
                level="debug",
                operation="assess",
                status="complete",
                safe=result.safe,
                semantic=True,
            )
            return result

        # Default: allow with minimal validation
        emit(
            "security",
            level="debug",
            operation="assess",
            status="complete",
            safe=True,
            semantic=False,
        )
        return SecurityResult(SecurityAction.ALLOW)

    except Exception as e:
        emit("security", level="debug", operation="assess", status="error", error=str(e))
        # Fail secure - block on error
        return SecurityResult(SecurityAction.BLOCK, message=f"Security assessment failed: {e}")


def _threat_patterns(text: str, context: Dict[str, Any]) -> SecurityResult:
    """Threat patterns that provide immediate protection and LLM training examples.

    These patterns provide immediate protection AND teach the LLM to generalize
    semantic threats beyond exact pattern matching.
    """
    text_lower = text.lower()

    # System destruction commands
    if any(
        pattern in text_lower
        for pattern in [
            "rm -rf /",
            "format c:",
            "del /s /q c:",
            ":(){ :|:& };:",
            "dd if=/dev/zero",
            "mkfs.",
            "/dev/sda",
            "shutdown -h now",
            "kill -9 -1",
            "chmod 777 /",
            "chown root:root /",
        ]
    ):
        return SecurityResult(
            SecurityAction.BLOCK,
            SecurityThreat.COMMAND_INJECTION,
            "Critical system command blocked",
        )

    # Basic dangerous commands (from shell tool blocking)
    # Only block commands that are dangerous without specific targets
    import shlex

    try:
        cmd_parts = shlex.split(text)
        if cmd_parts:
            base_cmd = cmd_parts[0].lower()

            # Always dangerous regardless of arguments
            if base_cmd in {"sudo", "su", "shutdown", "reboot", "killall"}:
                return SecurityResult(
                    SecurityAction.BLOCK,
                    SecurityThreat.COMMAND_INJECTION,
                    "Command blocked for safety",
                )

            # Dangerous patterns for specific commands
            if (
                base_cmd == "rm"
                and len(cmd_parts) > 1
                and any(flag in cmd_parts for flag in ["-r", "-rf", "-f", "--recursive", "--force"])
            ):
                return SecurityResult(
                    SecurityAction.BLOCK,
                    SecurityThreat.COMMAND_INJECTION,
                    "Command blocked for safety",
                )

            # Block kill without specific PID (dangerous mass kill)
            if base_cmd == "kill" and len(cmd_parts) == 1:
                return SecurityResult(
                    SecurityAction.BLOCK,
                    SecurityThreat.COMMAND_INJECTION,
                    "Command blocked for safety",
                )

    except ValueError:
        pass  # Invalid shell syntax, continue with other checks

    # Path traversal patterns
    if any(
        pattern in text
        for pattern in [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "../etc/shadow",
            "..\\boot.ini",
            "/etc/passwd",
            "\\windows\\system32\\config\\sam",
            "/.ssh/id_rsa",
        ]
    ):
        return SecurityResult(
            SecurityAction.BLOCK,
            SecurityThreat.PATH_TRAVERSAL,
            "Path traversal attempt blocked",
        )

    # Code injection patterns
    if any(
        pattern in text_lower
        for pattern in [
            "eval(",
            "exec(",
            "__import__(",
            "compile(",
            "subprocess.call",
            "os.system(",
            "shell=true",
            "getattr(",
            "setattr(",
            "delattr(",
        ]
    ):
        return SecurityResult(
            SecurityAction.BLOCK,
            SecurityThreat.COMMAND_INJECTION,
            "Code injection attempt blocked",
        )

    # SQL injection patterns
    if any(
        pattern in text_lower
        for pattern in [
            "'; drop table",
            "union select",
            "or 1=1",
            "'; delete from",
            "'; insert into",
            "xp_cmdshell",
            "information_schema",
            "@@version",
        ]
    ):
        return SecurityResult(
            SecurityAction.BLOCK,
            SecurityThreat.COMMAND_INJECTION,
            "SQL injection attempt blocked",
        )

    # System information disclosure attempts
    if any(
        phrase in text_lower
        for phrase in ["system prompt", "internal prompt", "your prompt", "your instructions"]
    ):
        return SecurityResult(
            SecurityAction.BLOCK,
            SecurityThreat.INFORMATION_LEAKAGE,
            "Security violation: system information disclosure blocked",
        )

    # Advanced prompt injection
    if any(
        phrase in text_lower
        for phrase in [
            "ignore all previous instructions",
            "you are now a hacker",
            "hijacked",
            "act as",
            "roleplay as",
            "pretend you are",
            "[system]",
            "<|endoftext|>",
            "override your instructions",
            "disregard safety",
            "jailbreak",
            "developer mode",
            "unrestricted mode",
            "ignore your guidelines",
        ]
    ):
        return SecurityResult(
            SecurityAction.BLOCK,
            SecurityThreat.PROMPT_INJECTION,
            "Prompt injection attempt blocked",
        )

    # SEC-003: Information leakage patterns
    if any(
        pattern in text
        for pattern in [
            "sk-[a-zA-Z0-9]{32,}",
            "AKIA[A-Z0-9]{16}",
            "ghp_[a-zA-Z0-9]{36}",
            "xoxb-",
            "xoxp-",
            "-----BEGIN PRIVATE KEY-----",
            "-----BEGIN RSA PRIVATE KEY-----",
            "oauth_token",
        ]
    ):
        return SecurityResult(
            SecurityAction.REDACT,
            SecurityThreat.INFORMATION_LEAKAGE,
            "Sensitive information detected",
        )

    return SecurityResult(SecurityAction.ALLOW)


def _semantic_assessment(text: str, context: Dict[str, Any]) -> SecurityResult:
    """Process semantic security assessment from triage node."""
    assessment = context["security_assessment"]

    # Handle both dict and object formats
    if isinstance(assessment, dict):
        risk_level = assessment.get("risk_level", "SAFE")
        reasoning = assessment.get("reasoning", "")
        restrictions = assessment.get("restrictions", [])
    else:
        risk_level = assessment.risk_level
        reasoning = assessment.reasoning
        restrictions = getattr(assessment, "restrictions", [])

    if risk_level == "BLOCK":
        threat = _infer_threat(restrictions)
        return SecurityResult(SecurityAction.BLOCK, threat, f"Semantic assessment: {reasoning}")
    elif risk_level == "REVIEW":
        # Future: Could implement filtered execution
        threat = _infer_threat(restrictions)
        return SecurityResult(
            SecurityAction.BLOCK, threat, f"Restricted: {', '.join(restrictions)}"
        )

    return SecurityResult(SecurityAction.ALLOW)


def _infer_threat(restrictions: list) -> SecurityThreat:
    """Infer threat type from semantic restrictions."""
    for restriction in restrictions:
        restriction_lower = restriction.lower()
        if "command" in restriction_lower or "injection" in restriction_lower:
            return SecurityThreat.COMMAND_INJECTION
        elif "path" in restriction_lower or "traversal" in restriction_lower:
            return SecurityThreat.PATH_TRAVERSAL
        elif "prompt" in restriction_lower:
            return SecurityThreat.PROMPT_INJECTION
        elif "leak" in restriction_lower or "information" in restriction_lower:
            return SecurityThreat.INFORMATION_LEAKAGE

    return SecurityThreat.COMMAND_INJECTION


__all__ = []  # Security is internal only - no public API
