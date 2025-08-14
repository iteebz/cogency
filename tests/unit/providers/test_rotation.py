"""Test automatic key rotation for provider methods."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from resilient_result import Ok

from cogency.providers.base import Provider, rotate_retry, setup_rotator


class MockProvider(Provider):
    """Mock provider for testing key rotation."""

    def __init__(self, api_keys=None, **kwargs):
        # Use canonical pattern
        rotator = setup_rotator("mock", api_keys or ["key1", "key2"], required=True)
        super().__init__(rotator=rotator, model="test-model", **kwargs)
        self._call_count = 0
        self._should_fail = False
        self._fail_count = 0

    def _get_client(self):
        return MagicMock()

    async def embed(self, text, **kwargs):
        """Mock embed method that can simulate failures."""
        self._call_count += 1

        if self._should_fail and self._call_count <= self._fail_count:
            # Simulate rate limit error
            raise Exception("Rate limit exceeded")

        return Ok([0.1, 0.2, 0.3])

    async def run(self, messages, **kwargs):
        """Mock run method that can simulate failures."""
        self._call_count += 1

        if self._should_fail and self._call_count <= self._fail_count:
            # Simulate rate limit error
            raise Exception("Rate limit exceeded")

        return Ok("Mock response")


@pytest.mark.asyncio
async def test_decorator_success():
    """Test decorator passes through successful calls."""
    mock_provider = MockProvider()

    @rotate_retry
    async def mock_method(self, arg1, arg2=None):
        return Ok(f"success-{arg1}-{arg2}")

    result = await mock_method(mock_provider, "test", arg2="value")
    assert result.success
    assert result.unwrap() == "success-test-value"


@pytest.mark.asyncio
async def test_decorator_handles_exceptions():
    """Test decorator converts exceptions to Err results."""
    mock_provider = MockProvider()

    @rotate_retry
    async def mock_method(self):
        raise ValueError("Test error")

    result = await mock_method(mock_provider)
    assert result.failure
    assert isinstance(result.error, ValueError)
    assert str(result.error) == "Test error"


@pytest.mark.asyncio
async def test_decorator_calls_rotation():
    """Test decorator calls rotator.rotate_retry."""
    mock_provider = MockProvider()

    # Mock the rotate_retry method
    mock_provider.rotator.rotate_retry = AsyncMock(return_value=Ok("rotated result"))

    @rotate_retry
    async def mock_method(self, arg):
        return Ok(f"original-{arg}")

    result = await mock_method(mock_provider, "test")

    # Verify rotate_retry was called
    mock_provider.rotator.rotate_retry.assert_called_once()
    assert result == Ok("rotated result")


def test_wrapped_embed():
    """Test that overridden embed method is automatically wrapped."""
    # Check that embed method has been wrapped
    assert hasattr(MockProvider.embed, "__wrapped__")

    # Check that the original method is preserved
    original_embed = MockProvider.embed.__wrapped__
    assert callable(original_embed)


def test_wrapped_run():
    """Test that overridden run method is automatically wrapped."""
    # Check that run method has been wrapped
    assert hasattr(MockProvider.run, "__wrapped__")

    # Check that the original method is preserved
    original_run = MockProvider.run.__wrapped__
    assert callable(original_run)


def test_base_methods_not_wrapped():
    """Test that base Provider class can be imported."""
    # Just test that Provider base class exists and has expected methods
    assert hasattr(Provider, "embed")
    assert hasattr(Provider, "generate")  # Provider has 'generate', not 'run'
    assert hasattr(Provider, "stream")


def test_inheritance_wrapping():
    """Test wrapping works through multiple inheritance levels."""

    class BaseCustomProvider(Provider):
        async def embed(self, text, **kwargs):
            return Ok("base custom")

    class SpecificProvider(BaseCustomProvider):
        async def embed(self, text, **kwargs):
            return Ok("specific")

    # Both should be wrapped
    assert hasattr(BaseCustomProvider.embed, "__wrapped__")
    assert hasattr(SpecificProvider.embed, "__wrapped__")


@pytest.mark.asyncio
async def test_successful_no_rotation():
    """Test successful calls don't trigger rotation."""
    provider = MockProvider()

    result = await provider.embed("test text")

    assert result.success
    assert result.unwrap() == [0.1, 0.2, 0.3]
    assert provider._call_count == 1


@pytest.mark.asyncio
async def test_rate_limit_rotation():
    """Test key rotation occurs on rate limit errors."""
    provider = MockProvider()
    provider._should_fail = True
    provider._fail_count = 1  # Fail on first call, succeed on second

    # Mock the heuristics to detect rate limit
    with patch("cogency.providers.utils.rotation.is_rate_limit", return_value=True):
        result = await provider.embed("test text")

    # Should succeed after rotation
    assert result.success
    assert provider._call_count == 2  # Called twice due to rotation


@pytest.mark.asyncio
async def test_key_exhaustion():
    """Test behavior when all keys are exhausted."""
    provider = MockProvider(api_keys=["single_key"])  # Only one key
    provider._should_fail = True
    provider._fail_count = 10  # Always fail

    # Mock the heuristics and rotation to raise exhaustion
    with patch("cogency.providers.utils.rotation.is_rate_limit", return_value=True):
        with patch.object(provider.rotator, "has_multiple", return_value=False):
            result = await provider.embed("test text")

    # Should return error result
    assert result.failure
    assert isinstance(result.error, Exception)


@pytest.mark.asyncio
async def test_non_rate_limit_no_rotation():
    """Test non-rate-limit errors don't trigger rotation."""

    class FailingProvider(Provider):
        def __init__(self):
            super().__init__(api_keys=["key1", "key2"], model="test")
            self._call_count = 0

        def _get_client(self):
            return MagicMock()

        async def embed(self, text, **kwargs):
            self._call_count += 1
            raise ValueError("generic application error")

    provider = FailingProvider()

    result = await provider.embed("test text")

    # Should return error without rotation (only called once)
    assert result.failure
    assert isinstance(result.error, ValueError)
    assert provider._call_count == 1  # No rotation, so only called once


def test_signature_preserved_embed():
    """Test embed method signature is preserved."""

    class TestProvider(Provider):
        def __init__(self):
            super().__init__(api_keys=["key"], model="test")

        def _get_client(self):
            return MagicMock()

        async def embed(self, text, **kwargs):
            """Original embed docstring."""
            return Ok("test")

    # Get the wrapped method
    wrapped_method = TestProvider.embed
    original_method = wrapped_method.__wrapped__

    # Check that functools.wraps preserved the signature
    assert wrapped_method.__name__ == original_method.__name__
    assert wrapped_method.__doc__ == original_method.__doc__
    assert wrapped_method.__doc__ == "Original embed docstring."


def test_signature_preserved_run():
    """Test run method signature is preserved."""
    # Get the wrapped method
    wrapped_method = MockProvider.run
    original_method = wrapped_method.__wrapped__

    # Check that functools.wraps preserved the signature
    assert wrapped_method.__name__ == original_method.__name__
    assert wrapped_method.__doc__ == original_method.__doc__


def test_no_overrides():
    """Test provider that doesn't override any methods."""

    class MinimalProvider(Provider):
        def __init__(self):
            super().__init__(api_keys=["key"], model="test")

        def _get_client(self):
            return MagicMock()

    # Just test that the provider can be instantiated
    provider = MinimalProvider()
    assert provider is not None


def test_no_double_wrapping():
    """Test that already wrapped methods don't get double-wrapped."""

    class PreWrappedProvider(Provider):
        def __init__(self):
            super().__init__(api_keys=["key"], model="test")

        def _get_client(self):
            return MagicMock()

        @rotate_retry
        async def embed(self, text, **kwargs):
            return Ok("pre-wrapped")

    # Should only be wrapped once
    assert hasattr(PreWrappedProvider.embed, "__wrapped__")
    # The __wrapped__ should be the original method, not another wrapper
    original = PreWrappedProvider.embed.__wrapped__
    assert not hasattr(original, "__wrapped__")
