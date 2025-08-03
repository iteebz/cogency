"""Security subsystem for agent protection.

Three-layer defense architecture:
- SEC-001: Input validation (prompt injection protection)
- SEC-002: Execution validation (command injection, path traversal prevention)  
- SEC-003: Output validation (information leakage, response hijacking detection)

The security module provides coordinated defense layers that work together to protect
agents from various attack vectors while maintaining usability for legitimate operations.

Note: Security functions are typically called automatically by the agent pipeline
rather than directly. The security_check() function provides unified validation
across all layers.
"""

# Public: Core security interfaces for agent protection
from .core import SecurityThreat, SecurityAction, SecurityResult, security_check
from .input import sanitize_user_input, secure  
from .execution import validate_tool_params
from .output import sanitize_output

# Internal: Implementation details - not exported in __all__
from .input import validate_input
from .execution import validate_execution
from .output import validate_output

__all__ = [
    # Public security coordination
    "SecurityThreat",
    "SecurityAction", 
    "SecurityResult",
    "security_check",
    
    # Public layer interfaces
    "sanitize_user_input", 
    "secure",
    "validate_tool_params",
    "sanitize_output",
]