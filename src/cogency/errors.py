"""Standardized error handling for Cogency tools and components."""

from typing import Any, Dict, Optional

from cogency.utils.results import RecoveryResult


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


class ToolError(CogencyError):
    """Error specific to tool execution."""

    pass


class ValidationError(CogencyError):
    """Error for input validation failures."""

    pass


class ConfigurationError(CogencyError):
    """Error for configuration-related issues."""

    pass


# Node-specific Errors for Granular Handling
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


class ActionError(CogencyError):
    """Error during action execution phase."""

    def __init__(
        self,
        message: str,
        failed_tools: list = None,
        recoverable: bool = True,
        **kwargs,
    ):
        super().__init__(message, error_code="ACTION_ERROR", **kwargs)
        self.failureed_tools = failed_tools or []
        self.recoverable = recoverable


class ResponseError(CogencyError):
    """Error during response generation phase."""

    def __init__(self, message: str, has_partial_response: bool = False, **kwargs):
        super().__init__(message, error_code="RESPONSE_ERROR", **kwargs)
        self.has_partial_response = has_partial_response


def format_error(error: Exception, tool_name: str, operation: str = None) -> Dict[str, Any]:
    """Standardized error formatting for tool responses.

    Args:
        error: The exception that occurred
        tool_name: Name of the tool where error occurred
        operation: Optional operation being performed

    Returns:
        Dict with standardized error format
    """
    error_response = {
        "error": str(error),
        "tool": tool_name,
        "error_type": type(error).__name__,
    }

    if operation:
        error_response["operation"] = operation

    if isinstance(error, CogencyError):
        error_response["error_code"] = error.error_code
        if error.details:
            error_response["details"] = error.details

    return error_response


def validate_params(params: Dict[str, Any], required: list[str], tool_name: str) -> None:
    """Validate that all required parameters are present and not empty.

    Args:
        params: Dictionary of parameters to validate
        required: List of required parameter names
        tool_name: Name of tool for error context

    Raises:
        ValidationError: If any required parameter is missing or empty
    """
    missing = []
    empty = []

    for param in required:
        if param not in params:
            missing.append(param)
        elif params[param] is None or (
            isinstance(params[param], str) and not params[param].strip()
        ):
            empty.append(param)

    if missing:
        raise ValidationError(
            f"Missing required parameters: {', '.join(missing)}",
            error_code="MISSING_PARAMETERS",
            details={"missing_params": missing, "tool": tool_name},
        )

    if empty:
        raise ValidationError(
            f"Empty required parameters: {', '.join(empty)}",
            error_code="EMPTY_PARAMETERS",
            details={"empty_params": empty, "tool": tool_name},
        )


def success_response(data: Dict[str, Any], message: str = None) -> Dict[str, Any]:
    """Create standardized success response format.

    Args:
        data: Response data
        message: Optional success message

    Returns:
        Dict with standardized success format
    """
    response = {**data, "success": True}
    if message:
        response["message"] = message
    return response


# Recovery Strategies for Node-specific Errors
def recover_from_preprocess_error(error: PreprocessError, state: Any) -> RecoveryResult:
    """Recovery strategy for preprocessing errors."""
    if error.memory_failed:
        # Continue without memory if memory fails
        state["memory_enabled"] = False
        return RecoveryResult.success(
            data=state, recovery_action="disable_memory", can_continue=True
        )

    # Default to continuing with empty context enrichment
    return RecoveryResult.success(data=state, recovery_action="skip_enrichment", can_continue=True)


def recover_from_reasoning_error(error: ReasoningError, state: Any) -> RecoveryResult:
    """Recovery strategy for reasoning errors."""
    if error.loop_detected:
        # Force respond mode if loop detected
        state["next_node"] = "respond"
        state["stopping_reason"] = "loop_recovery"
        return RecoveryResult.success(
            data=state, recovery_action="force_respond", can_continue=True
        )

    if error.mode == "deep":
        # Fall back to fast mode if deep mode fails
        state["react_mode"] = "fast"
        return RecoveryResult.success(
            data=state, recovery_action="fallback_to_fast", can_continue=True
        )

    # Default to responding directly
    state["next_node"] = "respond"
    state["stopping_reason"] = "reasoning_error"
    return RecoveryResult.success(data=state, recovery_action="direct_response", can_continue=True)


def recover_from_action_error(error: ActionError, state: Any) -> RecoveryResult:
    """Recovery strategy for action execution errors."""
    if not error.recoverable:
        # Non-recoverable error - force respond
        state["next_node"] = "respond"
        state["stopping_reason"] = "non_recoverable_action_error"
        return RecoveryResult.success(
            data=state, recovery_action="force_respond", can_continue=True
        )

    # Try reasoning again with error context
    state["execution_results"] = {
        "type": "error",
        "failed_tools": error.failureed_tools,
        "error_msg": error.message,
    }
    state["next_node"] = "reason"
    return RecoveryResult.success(data=state, recovery_action="retry_reasoning", can_continue=True)


def recover_from_response_error(error: ResponseError, state: Any) -> RecoveryResult:
    """Recovery strategy for response generation errors."""
    if error.has_partial_response:
        # Use partial response if available
        return RecoveryResult.success(data=state, recovery_action="use_partial", can_continue=True)

    # Generate fallback response
    state["direct_response"] = f"I encountered an issue generating a response: {error.message}"
    return RecoveryResult.success(
        data=state, recovery_action="fallback_response", can_continue=True
    )
