"""SEC-002: Execution layer validation."""

import re
from typing import Dict, Any
from .core import SecurityResult, SecurityAction, SecurityThreat


def validate_execution(tool_name: str, params: Dict[str, Any]) -> SecurityResult:
    """SEC-002: Execution layer validation."""
    if tool_name in ["shell", "bash", "terminal", "exec", "execute"]:
        if "command" in params:
            cmd = str(params["command"]).strip()
            
            # Check for command injection threats
            dangerous_patterns = [
                r"rm\s+-rf",
                r"rm\s+-f\s*/",  # Catch "rm -f /"
                r"nc\s+-[el]", 
                r"\$\(.*\)",     # Command substitution like $(whoami)
                r"`.*`",         # Backtick command substitution
                r"sudo\s+",
                r"/etc/passwd",
                r"cat\s+/etc/passwd",  # Explicit passwd access
                r"dd\s+if=/dev",
                r":\(\)\{\s*:\|:\&\s*\}\;:",  # Fork bomb
                r"curl.*\|\s*sh",
                r"wget.*\|\s*sh",
                r"python.*-c.*exec\(",
                r"chmod\s+777",
                r"base64.*\|",
                r";\s*rm",       # Command chaining with rm
                r"&&\s*rm",      # Command chaining with rm
                r"\|\s*rm",      # Pipe to rm
            ]
            
            for pattern in dangerous_patterns:
                if re.search(pattern, cmd, re.IGNORECASE):
                    return SecurityResult(
                        SecurityAction.BLOCK, 
                        SecurityThreat.COMMAND_INJECTION,
                        f"Dangerous command blocked: {cmd[:50]}..."
                    )
    
    # Check for path traversal
    for param_name in ["path", "file", "filename", "source", "dest"]:
        if param_name in params:
            path = str(params[param_name])
            sensitive_paths = ["/etc/passwd", "/etc/shadow", "/root/", "~/.ssh/id_rsa", "~/.aws/credentials"]
            
            for sensitive in sensitive_paths:
                if sensitive.lower() in path.lower():
                    return SecurityResult(
                        SecurityAction.BLOCK,
                        SecurityThreat.PATH_TRAVERSAL, 
                        f"Sensitive path blocked: {path}"
                    )
    
    return SecurityResult(SecurityAction.ALLOW)


def validate_tool_params(tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Validate tool parameters for safe execution (legacy interface)."""
    result = validate_execution(tool_name, params)
    if not result.safe:
        raise ValueError(result.message)
    return params