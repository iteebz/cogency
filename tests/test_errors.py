"""Test error handling and standardization."""

import pytest

from cogency.errors import (
    CogencyError,
    ConfigurationError,
    ToolError,
    ValidationError,
    format_error,
    success_response,
    validate_params,
)


def test_cogency_error_basic():
    """Test basic error creation."""
    error = CogencyError("test message")
    assert str(error) == "test message"
    assert error.error_code == "GENERAL_ERROR"
    assert error.details == {}


def test_cogency_error_with_details():
    """Test error with custom details."""
    details = {"field": "value"}
    error = CogencyError("test message", error_code="CUSTOM_ERROR", details=details)
    assert error.error_code == "CUSTOM_ERROR"
    assert error.details == details


def test_error_inheritance():
    """Test all error types inherit from CogencyError."""
    assert isinstance(ToolError("test"), CogencyError)
    assert isinstance(ValidationError("test"), CogencyError)
    assert isinstance(ConfigurationError("test"), CogencyError)


def test_format_error():
    """Test error formatting."""
    error = ValueError("test error")
    result = format_error(error, "test_tool")

    assert result["error"] == "test error"
    assert result["tool"] == "test_tool"
    assert result["error_type"] == "ValueError"


def test_format_error_with_operation():
    """Test error formatting with operation."""
    error = RuntimeError("runtime issue")
    result = format_error(error, "test_tool", "execute")

    assert result["operation"] == "execute"
    assert result["error"] == "runtime issue"


def test_validate_params():
    """Test parameter validation function."""
    # Success case
    params = {"required1": "value1", "required2": "value2"}
    validate_params(params, ["required1", "required2"], "test_tool")

    # Missing parameter
    with pytest.raises(ValidationError) as exc_info:
        validate_params({"required1": "value1"}, ["required1", "required2"], "test_tool")
    assert "Missing required parameters: required2" in str(exc_info.value)

    # Empty parameter
    with pytest.raises(ValidationError) as exc_info:
        validate_params(
            {"required1": "value1", "required2": ""},
            ["required1", "required2"],
            "test_tool",
        )
    assert "Empty required parameters: required2" in str(exc_info.value)


def test_success_response_format():
    """Test success response formatting."""
    # Basic response
    data = {"result": "test", "count": 5}
    result = success_response(data)
    expected = {"result": "test", "count": 5, "success": True}
    assert result == expected

    # With message
    result = success_response({"result": "test"}, "Operation completed")
    assert result["success"] is True
    assert result["message"] == "Operation completed"
