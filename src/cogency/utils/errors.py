"""Standardized error handling for Cogency tools and components."""

import logging
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


class ToolError(CogencyError):
    """Error specific to tool execution."""

    pass


class ValidationError(CogencyError):
    """Error for input validation failures."""

    pass


class ConfigurationError(CogencyError):
    """Error for configuration-related issues."""

    pass


def format_tool_error(error: Exception, tool_name: str, operation: str = None) -> Dict[str, Any]:
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


def handle_tool_exception(func):
    """Decorator to handle exceptions in tool methods with standardized error formatting."""

    async def wrapper(self, *args, **kwargs):
        try:
            return await func(self, *args, **kwargs)
        except Exception as e:
            tool_name = getattr(self, "name", self.__class__.__name__)
            operation = func.__name__

            # Log the full traceback for debugging
            logging.error(f"Error in {tool_name}.{operation}: {e}", exc_info=True)

            return format_tool_error(e, tool_name, operation)

    return wrapper


def validate_required_params(params: Dict[str, Any], required: list[str], tool_name: str) -> None:
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


def create_success_response(data: Dict[str, Any], message: str = None) -> Dict[str, Any]:
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
