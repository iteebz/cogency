"""Test error handling and standardization."""

import pytest

from cogency.resilience import (
    ActionError,
    CogencyError,
    ConfigError,
    ParsingError,
)
from cogency.utils.formatting import format_tool_error


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
    assert isinstance(ActionError("test"), CogencyError)
    assert isinstance(ParsingError("test"), CogencyError)
    assert isinstance(ConfigError("test"), CogencyError)


def test_format_tool_error():
    """Test tool error formatting."""
    error = ValueError("test error")
    result = format_tool_error("test_tool", error)

    assert "test_tool" in result
    assert isinstance(result, str)


def test_config_error():
    """Test ConfigError with config field."""
    error = ConfigError("Invalid setting", config_field="timeout")
    assert str(error) == "Invalid setting"
    assert error.error_code == "CONFIG_ERROR"
    assert error.config_field == "timeout"


def test_parsing_error():
    """Test ParsingError with raw response."""
    error = ParsingError("Invalid JSON", raw_response='{"invalid": }', correction_attempts=2)
    assert str(error) == "Invalid JSON"
    assert error.error_code == "JSON_PARSING_ERROR"
    assert error.raw_response == '{"invalid": }'
    assert error.correction_attempts == 2
