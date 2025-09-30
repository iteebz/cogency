from __future__ import annotations


class CogencyError(RuntimeError):
    def __init__(
        self, message: str, *, cause: Exception | None = None, original_json: str | None = None
    ) -> None:
        super().__init__(message)
        self.cause = cause
        self.original_json = original_json


class AgentError(CogencyError):
    pass


class ToolError(CogencyError):
    pass


class ProviderError(CogencyError):
    pass


class ProfileError(CogencyError):
    pass


class ProtocolError(CogencyError):
    pass
