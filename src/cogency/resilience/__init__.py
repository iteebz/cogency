"""Beautiful resilience - world-class simplicity built on resilient-result."""

# Import resilient-result for internal use only

# No local decorators - use resilient-result directly or agent.* patterns
from cogency.decorators import act, preprocess, reason, respond, robust
from .exceptions import (
    ActionError,
    CogencyError,
    ConfigError,
    ParsingError,
    PreprocessError,
    ReasoningError,
    ResponseError,
)
from .recovery import recovery

__all__ = [
    "CogencyError",
    "ActionError",
    "ConfigError",
    "ParsingError",
    "PreprocessError",
    "ReasoningError",
    "ResponseError",
    "recovery",
    "robust",
    "act",
    "preprocess",
    "reason",
    "respond",
    # No resilient-result re-exports - import directly from resilient_result
]
