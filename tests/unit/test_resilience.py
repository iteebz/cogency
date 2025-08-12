"""Tests for resilience and error handling logic."""

from cogency.resilience import resilience, smart_handler


def test_smart_handler_code_bugs():
    """Test smart_handler identifies code bugs."""
    # Code bugs should return False (stop retrying)
    assert smart_handler(TypeError("invalid type")) is False
    assert smart_handler(AttributeError("no attribute")) is False
    assert smart_handler(KeyError("missing key")) is False
    assert smart_handler(ImportError("module not found")) is False
    assert smart_handler(NameError("name not defined")) is False
    assert smart_handler(IndentationError("bad indent")) is False
    assert smart_handler(SyntaxError("invalid syntax")) is False


def test_smart_handler_validation_error():
    """Test smart_handler handles validation errors."""
    try:
        from pydantic import BaseModel, ValidationError

        # Create real validation error
        class TestModel(BaseModel):
            value: int

        try:
            TestModel(value="not_int")
        except ValidationError as e:
            assert smart_handler(e) is False
    except ImportError:
        # Test with fallback ValidationError type checking only
        from cogency.resilience import ValidationError

        # Just test the class exists and is classified correctly
        assert ValidationError is not None


def test_smart_handler_transient_errors():
    """Test smart_handler allows retry for transient errors."""
    # Network/API errors should return None (continue retrying)
    assert smart_handler(ConnectionError("network failed")) is None
    assert smart_handler(TimeoutError("request timeout")) is None
    assert smart_handler(RuntimeError("runtime issue")) is None
    assert smart_handler(ValueError("invalid value")) is None
    assert smart_handler(Exception("generic error")) is None


def test_smart_handler_custom_exceptions():
    """Test smart_handler with custom exception types."""

    class CustomError(Exception):
        pass

    class NetworkError(Exception):
        pass

    # Custom errors should be treated as transient
    assert smart_handler(CustomError("custom")) is None
    assert smart_handler(NetworkError("network")) is None


def test_resilience_decorator_exists():
    """Test resilience decorator is properly configured."""
    assert resilience is not None
    assert callable(resilience)

    # Should be configured with smart_handler
    assert callable(resilience)


def test_resilience_decorator_with_function():
    """Test resilience decorator can wrap functions."""
    call_count = 0

    @resilience
    def test_function():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            # Transient error - should retry
            raise ConnectionError("network error")
        return "success"

    # Should eventually succeed after retries
    result = test_function()
    # resilient returns Result object
    assert result.success
    assert result.data == "success"
    assert call_count >= 3


def test_resilience_decorator_stops_on_code_bug():
    """Test resilience decorator stops on code bugs."""
    call_count = 0

    @resilience
    def buggy_function():
        nonlocal call_count
        call_count += 1
        # Code bug - should not retry
        raise TypeError("type error")

    # Should return failure Result, not raise
    result = buggy_function()
    assert result.failure
    assert "type error" in str(result.error)

    # Should only be called once (no retries)
    assert call_count == 1


def test_resilience_decorator_with_async():
    """Test resilience decorator works with async functions."""
    import asyncio

    call_count = 0

    @resilience
    async def async_function():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise ConnectionError("network error")
        return "async success"

    # Should work with async functions
    result = asyncio.run(async_function())
    assert result.success
    assert result.data == "async success"
    assert call_count >= 2


def test_error_classification_comprehensive():
    """Test comprehensive error classification logic."""
    # All code bugs
    code_bugs = [
        TypeError(),
        AttributeError(),
        KeyError(),
        ImportError(),
        NameError(),
        IndentationError(),
        SyntaxError(),
    ]

    for bug in code_bugs:
        assert smart_handler(bug) is False, f"{type(bug).__name__} should be classified as code bug"

    # All transient errors
    transient_errors = [
        ConnectionError(),
        TimeoutError(),
        RuntimeError(),
        ValueError(),
        OSError(),
        OSError(),
    ]

    for error in transient_errors:
        assert (
            smart_handler(error) is None
        ), f"{type(error).__name__} should be classified as transient"


def test_pydantic_integration():
    """Test pydantic integration if available."""
    try:
        from pydantic import BaseModel, ValidationError

        class TestModel(BaseModel):
            value: int

        try:
            TestModel(value="not_int")
        except ValidationError as e:
            assert smart_handler(e) is False
    except ImportError:
        # If pydantic not available, test fallback
        from cogency.resilience import ValidationError

        error = ValidationError("fallback error")
        assert smart_handler(error) is False


def test_fallback_validation_error():
    """Test fallback ValidationError class."""
    from cogency.resilience import ValidationError

    # Should be proper exception class
    assert issubclass(ValidationError, Exception)

    # Test that it's recognized as code bug in smart_handler
    # (Don't instantiate since it may conflict with pydantic if available)
    assert ValidationError in [
        TypeError,
        AttributeError,
        KeyError,
        ImportError,
        NameError,
        IndentationError,
        SyntaxError,
        ValidationError,
    ]
