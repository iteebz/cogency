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
from .recovery import recover

# User formatting moved to utils.formatting
from .safe import safe, unwrap

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
    "unwrap",
    # User formatting no longer exported from resilience layer
    "Result",
    "Ok",
    "Err",
    "resilient",
]
