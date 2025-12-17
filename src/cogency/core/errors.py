"""Exception hierarchy for structured error handling."""


class CogencyError(Exception):
    """Base exception for all Cogency errors."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class StorageError(CogencyError):
    """Storage failure. Set retryable=True for transient errors (locks, network)."""

    def __init__(
        self, message: str, *, cause: Exception | None = None, retryable: bool = False
    ) -> None:
        super().__init__(message, cause=cause)
        self.retryable = retryable


class LLMError(CogencyError):
    """LLM provider error. Flags: rate_limited, auth_failed."""

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
        rate_limited: bool = False,
        auth_failed: bool = False,
    ) -> None:
        super().__init__(message, cause=cause)
        self.rate_limited = rate_limited
        self.auth_failed = auth_failed


class ToolError(CogencyError):
    """Tool execution failure. Flags: validation_failed, timeout."""

    def __init__(
        self,
        message: str,
        *,
        cause: Exception | None = None,
        validation_failed: bool = False,
        timeout: bool = False,
    ) -> None:
        super().__init__(message, cause=cause)
        self.validation_failed = validation_failed
        self.timeout = timeout


class ProtocolError(CogencyError):
    """Protocol parsing failure. Preserves original_input for debugging."""

    def __init__(
        self, message: str, *, cause: Exception | None = None, original_input: str | None = None
    ) -> None:
        super().__init__(message, cause=cause)
        self.original_input = original_input


class ConfigError(CogencyError):
    """Invalid configuration. Raised at initialization."""


__all__ = [
    "CogencyError",
    "ConfigError",
    "LLMError",
    "ProtocolError",
    "StorageError",
    "ToolError",
]
