"""Tests for error handling utilities."""

from unittest.mock import patch

import pytest

from cogency.utils.errors import (
    CogencyError,
    ConfigurationError,
    ToolError,
    ValidationError,
    create_success_response,
    format_tool_error,
    handle_tool_exception,
    validate_required_params,
)


class TestCogencyError:
    """Test suite for CogencyError base exception."""

    def test_cogency_error_basic(self):
        """Test basic CogencyError creation."""
        error = CogencyError("Test error message")

        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.error_code == "GENERAL_ERROR"
        assert error.details == {}

    def test_cogency_error_with_code_and_details(self):
        """Test CogencyError with custom code and details."""
        details = {"param": "value", "count": 42}
        error = CogencyError("Custom error", error_code="CUSTOM_ERROR", details=details)

        assert error.message == "Custom error"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.details == details

    def test_tool_error_inheritance(self):
        """Test ToolError inherits from CogencyError."""
        error = ToolError("Tool failed", error_code="TOOL_FAILED")

        assert isinstance(error, CogencyError)
        assert error.message == "Tool failed"
        assert error.error_code == "TOOL_FAILED"

    def test_validation_error_inheritance(self):
        """Test ValidationError inherits from CogencyError."""
        error = ValidationError("Invalid input", error_code="INVALID_INPUT")

        assert isinstance(error, CogencyError)
        assert error.message == "Invalid input"
        assert error.error_code == "INVALID_INPUT"

    def test_configuration_error_inheritance(self):
        """Test ConfigurationError inherits from CogencyError."""
        error = ConfigurationError("Bad config", error_code="BAD_CONFIG")

        assert isinstance(error, CogencyError)
        assert error.message == "Bad config"
        assert error.error_code == "BAD_CONFIG"


class TestFormatToolError:
    """Test suite for format_tool_error function."""

    def test_format_tool_error_basic(self):
        """Test basic tool error formatting."""
        error = Exception("Something went wrong")

        result = format_tool_error(error, "test_tool")

        assert result["error"] == "Something went wrong"
        assert result["tool"] == "test_tool"
        assert result["error_type"] == "Exception"

    def test_format_tool_error_with_operation(self):
        """Test tool error formatting with operation."""
        error = ValueError("Invalid value")

        result = format_tool_error(error, "calculator", "add")

        assert result["error"] == "Invalid value"
        assert result["tool"] == "calculator"
        assert result["operation"] == "add"
        assert result["error_type"] == "ValueError"

    def test_format_tool_error_cogency_error(self):
        """Test formatting CogencyError with additional details."""
        details = {"input": "invalid", "expected": "number"}
        error = ValidationError(
            "Invalid input provided", error_code="INVALID_INPUT", details=details
        )

        result = format_tool_error(error, "validator", "validate")

        assert result["error"] == "Invalid input provided"
        assert result["tool"] == "validator"
        assert result["operation"] == "validate"
        assert result["error_type"] == "ValidationError"
        assert result["error_code"] == "INVALID_INPUT"
        assert result["details"] == details


class TestHandleToolException:
    """Test suite for handle_tool_exception decorator."""

    @pytest.mark.asyncio
    async def test_handle_tool_exception_success(self):
        """Test decorator with successful function execution."""

        class TestTool:
            name = "test_tool"

            @handle_tool_exception
            async def test_method(self, value):
                return {"result": value * 2}

        tool = TestTool()
        result = await tool.test_method(5)

        assert result == {"result": 10}

    @pytest.mark.asyncio
    async def test_handle_tool_exception_with_exception(self):
        """Test decorator with exception handling."""

        class TestTool:
            name = "test_tool"

            @handle_tool_exception
            async def test_method(self, value):
                raise ValueError("Test error")

        tool = TestTool()

        with patch("cogency.utils.errors.logging.error") as mock_log:
            result = await tool.test_method(5)

        assert "error" in result
        assert result["error"] == "Test error"
        assert result["tool"] == "test_tool"
        assert result["operation"] == "test_method"
        assert result["error_type"] == "ValueError"

        # Verify logging was called
        mock_log.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_tool_exception_no_name_attribute(self):
        """Test decorator with object that has no name attribute."""

        class TestTool:
            @handle_tool_exception
            async def test_method(self):
                raise Exception("Test error")

        tool = TestTool()

        with patch("cogency.utils.errors.logging.error"):
            result = await tool.test_method()

        assert result["tool"] == "TestTool"  # Uses class name as fallback

    @pytest.mark.asyncio
    async def test_handle_tool_exception_cogency_error(self):
        """Test decorator with CogencyError."""

        class TestTool:
            name = "test_tool"

            @handle_tool_exception
            async def test_method(self):
                raise ToolError("Tool failed", error_code="TOOL_FAILED", details={"retry": True})

        tool = TestTool()

        with patch("cogency.utils.errors.logging.error"):
            result = await tool.test_method()

        assert result["error"] == "Tool failed"
        assert result["error_code"] == "TOOL_FAILED"
        assert result["details"] == {"retry": True}


class TestValidateRequiredParams:
    """Test suite for validate_required_params function."""

    def test_validate_required_params_success(self):
        """Test successful parameter validation."""
        params = {"name": "John", "age": 30, "city": "NYC"}
        required = ["name", "age"]

        # Should not raise any exception
        validate_required_params(params, required, "test_tool")

    def test_validate_required_params_missing(self):
        """Test validation with missing parameters."""
        params = {"name": "John"}
        required = ["name", "age", "city"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_params(params, required, "test_tool")

        error = exc_info.value
        assert error.error_code == "MISSING_PARAMETERS"
        assert "age" in error.details["missing_params"]
        assert "city" in error.details["missing_params"]
        assert error.details["tool"] == "test_tool"

    def test_validate_required_params_empty_string(self):
        """Test validation with empty string parameters."""
        params = {"name": "", "age": 30, "city": "  "}
        required = ["name", "age", "city"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_params(params, required, "test_tool")

        error = exc_info.value
        assert error.error_code == "EMPTY_PARAMETERS"
        assert "name" in error.details["empty_params"]
        assert "city" in error.details["empty_params"]
        assert "age" not in error.details["empty_params"]

    def test_validate_required_params_none_value(self):
        """Test validation with None values."""
        params = {"name": "John", "age": None}
        required = ["name", "age"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_params(params, required, "test_tool")

        error = exc_info.value
        assert error.error_code == "EMPTY_PARAMETERS"
        assert "age" in error.details["empty_params"]

    def test_validate_required_params_mixed_errors(self):
        """Test validation with both missing and empty parameters."""
        params = {"name": "", "age": 30}  # Missing city, empty name
        required = ["name", "age", "city"]

        with pytest.raises(ValidationError) as exc_info:
            validate_required_params(params, required, "test_tool")

        error = exc_info.value
        # Should prioritize missing parameters
        assert error.error_code == "MISSING_PARAMETERS"
        assert "city" in error.details["missing_params"]

    def test_validate_required_params_empty_required_list(self):
        """Test validation with empty required list."""
        params = {"name": "John"}
        required = []

        # Should not raise any exception
        validate_required_params(params, required, "test_tool")


class TestCreateSuccessResponse:
    """Test suite for create_success_response function."""

    def test_create_success_response_basic(self):
        """Test basic success response creation."""
        data = {"result": 42, "operation": "add"}

        result = create_success_response(data)

        assert result["success"] is True
        assert result["result"] == 42
        assert result["operation"] == "add"

    def test_create_success_response_with_message(self):
        """Test success response with message."""
        data = {"result": "file created"}
        message = "Operation completed successfully"

        result = create_success_response(data, message)

        assert result["success"] is True
        assert result["result"] == "file created"
        assert result["message"] == message

    def test_create_success_response_empty_data(self):
        """Test success response with empty data."""
        result = create_success_response({})

        assert result["success"] is True
        assert len(result) == 1  # Only success field

    def test_create_success_response_overwrite_success(self):
        """Test that success field cannot be overwritten."""
        data = {"success": False, "result": "test"}

        result = create_success_response(data)

        # success should be True regardless of input
        assert result["success"] is True
        assert result["result"] == "test"
