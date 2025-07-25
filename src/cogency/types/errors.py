"""Standardized error handling for Cogency tools and components."""

import re
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


class ParsingError(CogencyError):
    """Error during JSON parsing phase - separate from reasoning logic errors."""

    def __init__(
        self,
        message: str,
        raw_response: str = None,
        correction_attempts: int = 0,
        fallback_used: str = None,
        **kwargs,
    ):
        super().__init__(message, error_code="JSON_PARSING_ERROR", **kwargs)
        self.raw_response = raw_response
        self.correction_attempts = correction_attempts
        self.fallback_used = fallback_used


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
        self.failed_tools = failed_tools or []
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
        "failed_tools": error.failed_tools,
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


# Error message templates for user-friendly display
ERROR_TEMPLATES = {
    # Tool errors
    "TOOL_EXECUTION_FAILED": "I couldn't complete the {tool_name} operation. {reason}",
    "TOOL_TIMEOUT": "The {tool_name} operation timed out. This usually means the request is taking longer than expected.",
    "TOOL_INVALID_ARGS": "I couldn't run {tool_name} because some required information is missing: {missing_params}",
    "TOOL_API_ERROR": "I encountered an issue connecting to {service_name}. Please check your network connection or try again.",
    # LLM errors
    "LLM_API_ERROR": "I'm having trouble connecting to the AI service. Please try again in a moment.",
    "LLM_QUOTA_EXCEEDED": "The AI service is temporarily at capacity. Please try again later.",
    "LLM_INVALID_RESPONSE": "I received an unexpected response format. Let me try a different approach.",
    # Reasoning errors
    "REASONING_LOOP": "I noticed I was repeating the same approach. Let me try a different strategy.",
    "MAX_ITERATIONS": "I've tried several approaches but haven't found a complete solution. Here's what I can tell you so far.",
    "PARSING_ERROR": "I had trouble understanding the response format. Let me rephrase that.",
    # JSON Parsing specific errors
    "JSON_PARSE_FAILED": "I had trouble formatting my response properly. Let me try again.",
    "JSON_SELF_CORRECTION_FAILED": "I attempted to fix my response format but couldn't resolve it. Continuing with best effort.",
    "JSON_FALLBACK_USED": "I used an alternative parsing method to understand the response.",
    # Memory errors
    "MEMORY_UNAVAILABLE": "I couldn't access memory for this conversation, but I can still help you.",
    "MEMORY_SEARCH_FAILED": "I had trouble searching my memory, but I'll work with what I know.",
    # Generic fallbacks
    "UNKNOWN_ERROR": "I encountered an unexpected issue. Let me try to help you anyway.",
    "TEMPORARY_ISSUE": "I'm experiencing a temporary issue. Please try again.",
}


def get_user_friendly_message(
    error_type: str, context: Optional[Dict[str, Any]] = None, original_error: Optional[str] = None
) -> str:
    """Convert technical errors to user-friendly messages.

    Args:
        error_type: Error type key from ERROR_TEMPLATES
        context: Context variables for message formatting
        original_error: Original technical error for fallback

    Returns:
        User-friendly error message
    """
    context = context or {}

    # Get template or fallback
    template = ERROR_TEMPLATES.get(error_type, ERROR_TEMPLATES["UNKNOWN_ERROR"])

    try:
        # Format template with context
        message = template.format(**context)
        return message
    except KeyError:
        # Fallback if formatting fails
        if original_error:
            return f"I encountered an issue: {_sanitize_error(original_error)}"
        return ERROR_TEMPLATES["UNKNOWN_ERROR"]


def _sanitize_error(error_msg: str) -> str:
    """Remove technical jargon from error messages."""
    # Remove common technical patterns
    patterns_to_remove = [
        r"Traceback \(most recent call last\):.*",
        r'File ".*", line \d+.*',
        r"AttributeError:.*",
        r"ValueError:.*",
        r"KeyError:.*",
        r"TypeError:.*",
    ]

    for pattern in patterns_to_remove:
        error_msg = re.sub(pattern, "", error_msg, flags=re.DOTALL)

    # Clean up extra whitespace
    error_msg = " ".join(error_msg.split())

    # Truncate very long messages
    if len(error_msg) > 200:
        error_msg = error_msg[:200] + "..."

    return error_msg or "An unexpected issue occurred"


def format_tool_error(tool_name: str, error: Exception, operation: str = None) -> str:
    """Format tool errors for user display."""
    error_str = str(error).lower()

    # Detect common error patterns
    if "timeout" in error_str or "timed out" in error_str:
        return get_user_friendly_message("TOOL_TIMEOUT", {"tool_name": tool_name})
    elif "connection" in error_str or "network" in error_str:
        return get_user_friendly_message("TOOL_API_ERROR", {"service_name": tool_name})
    elif "missing" in error_str or "required" in error_str:
        return get_user_friendly_message(
            "TOOL_INVALID_ARGS", {"tool_name": tool_name, "missing_params": "see details above"}
        )
    else:
        reason = _sanitize_error(str(error))
        return get_user_friendly_message(
            "TOOL_EXECUTION_FAILED", {"tool_name": tool_name, "reason": reason}
        )


def format_reasoning_error(error_type: str, details: Dict[str, Any] = None) -> str:
    """Format reasoning errors for user display."""
    details = details or {}

    if error_type == "loop_detected":
        return get_user_friendly_message("REASONING_LOOP")
    elif error_type == "max_iterations":
        return get_user_friendly_message("MAX_ITERATIONS")
    elif error_type == "json_parse_error":
        return get_user_friendly_message("PARSING_ERROR")
    else:
        return get_user_friendly_message("UNKNOWN_ERROR")


def format_parsing_error(error_type: str, details: Dict[str, Any] = None) -> str:
    """Format JSON parsing errors for user display - separate from reasoning errors."""
    details = details or {}

    if error_type == "json_parse_failed":
        return get_user_friendly_message("JSON_PARSE_FAILED")
    elif error_type == "self_correction_failed":
        return get_user_friendly_message("JSON_SELF_CORRECTION_FAILED")
    elif error_type == "fallback_used":
        return get_user_friendly_message("JSON_FALLBACK_USED")
    else:
        return get_user_friendly_message("PARSING_ERROR")
