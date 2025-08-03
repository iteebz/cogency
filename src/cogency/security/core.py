"""Core security types and coordinator."""

from enum import Enum
from typing import Dict, Any


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
    FILTER = "filter" 
    BLOCK = "block"
    REDACT = "redact"


class SecurityResult:
    """Security validation result."""
    def __init__(self, action: SecurityAction, threat: SecurityThreat = None, message: str = ""):
        self.action = action
        self.threat = threat
        self.message = message
        self.safe = action == SecurityAction.ALLOW
    
    def __bool__(self):
        return self.safe


def security_check(layer: str, **kwargs) -> SecurityResult:
    """Unified security validation across all layers."""
    from .input import validate_input
    from .execution import validate_execution  
    from .output import validate_output
    
    if layer == "input" and "text" in kwargs:
        return validate_input(kwargs["text"])
    elif layer == "execution" and "tool_name" in kwargs and "params" in kwargs:
        return validate_execution(kwargs["tool_name"], kwargs["params"])
    elif layer == "output" and "text" in kwargs:
        return validate_output(kwargs["text"])
    else:
        return SecurityResult(SecurityAction.ALLOW, message="Unknown security layer")