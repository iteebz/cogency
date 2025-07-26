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

# User formatting moved to utils.formatting
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
    # User formatting no longer exported from resilience layer
    "Result",
    "Ok",
    "Err",
    "resilient",
]
