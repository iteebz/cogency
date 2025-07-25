"""Clean exception hierarchy - 6 focused classes."""

from typing import Any, Dict, Optional


class CogencyError(Exception):
    """Base exception for Cogency-specific errors."""

    def __init__(
        self,
        message: str,
        error_code: str = "GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class PreprocessError(CogencyError):
    """Error during preprocessing phase."""

    def __init__(self, message: str, memory_failed: bool = False, **kwargs):
        super().__init__(message, error_code="PREPROCESS_ERROR", **kwargs)
        self.memory_failed = memory_failed


class ReasoningError(CogencyError):
    """Error during reasoning phase."""

    def __init__(self, message: str, mode: str = "unknown", loop_detected: bool = False, **kwargs):
        super().__init__(message, error_code="REASONING_ERROR", **kwargs)
        self.mode = mode
        self.loop_detected = loop_detected


class ParsingError(CogencyError):
    """Error during JSON parsing phase."""

    def __init__(
        self, message: str, raw_response: str = None, correction_attempts: int = 0, **kwargs
    ):
        super().__init__(message, error_code="JSON_PARSING_ERROR", **kwargs)
        self.raw_response = raw_response
        self.correction_attempts = correction_attempts


class ActionError(CogencyError):
    """Error during action execution phase."""

    def __init__(self, message: str, failed_tools: list = None, recoverable: bool = True, **kwargs):
        super().__init__(message, error_code="ACTION_ERROR", **kwargs)
        self.failed_tools = failed_tools or []
        self.recoverable = recoverable


class ResponseError(CogencyError):
    """Error during response generation phase."""

    def __init__(self, message: str, has_partial_response: bool = False, **kwargs):
        super().__init__(message, error_code="RESPONSE_ERROR", **kwargs)
        self.has_partial_response = has_partial_response


class ConfigError(CogencyError):
    """Error in configuration or setup phase."""

    def __init__(self, message: str, config_field: str = None, **kwargs):
        super().__init__(message, error_code="CONFIG_ERROR", **kwargs)
        self.config_field = config_field
