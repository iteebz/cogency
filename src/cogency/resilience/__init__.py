"""Beautiful resilience - world-class simplicity built on resilient-result."""

# Re-export resilient-result - no local duplication
from resilient_result import Err, Ok, Result, resilient

from .checkpoint import resume
from .exceptions import (
    ActionError,
    CogencyError,
    ConfigError,
    ParsingError,
    PreprocessError,
    ReasoningError,
    ResponseError,
)
from .formatting import format_tool_error, get_user_message
from .patterns import safe
from .recovery import recover

__all__ = [
    "CogencyError",
    "ActionError",
    "ConfigError",
    "ParsingError",
    "PreprocessError",
    "ReasoningError",
    "ResponseError",
    "recover",
    "resume",
    "safe",
    "get_user_message",
    "format_tool_error",
    "Result",
    "Ok",
    "Err",
    "resilient",
]
