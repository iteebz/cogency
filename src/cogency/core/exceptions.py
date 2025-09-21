"""Domain-specific exception hierarchy for cogency."""

from __future__ import annotations


class CogencyError(RuntimeError):
    """Base class for all cogency errors."""

    def __init__(self, message: str, *, cause: Exception | None = None) -> None:
        super().__init__(message)
        self.cause = cause


class AgentError(CogencyError):
    """Raised when agent orchestration fails."""


class ToolError(CogencyError):
    """Raised when a tool invocation fails."""


class ProviderError(CogencyError):
    """Raised when an upstream model provider fails."""


class ProfileError(CogencyError):
    """Raised when profile learning cannot complete."""
