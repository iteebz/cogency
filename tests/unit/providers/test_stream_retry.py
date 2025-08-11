"""Test stream retry functionality with seamless resumption."""

from unittest.mock import patch

import pytest

from cogency.providers.base import Provider, setup_rotator
from cogency.providers.rotation import KeyRotationError


class StreamMockProvider(Provider):
    """Mock provider that can simulate streaming failures."""

    def __init__(self, api_keys=None, fail_after_chunks=None, **kwargs):
        rotator = setup_rotator("stream-mock", api_keys or ["key1", "key2", "key3"], required=True)
        super().__init__(rotator=rotator, model="stream-test-model", **kwargs)
        self.fail_after_chunks = fail_after_chunks
        self.call_count = 0
        self.chunks = ["Hello", " there", "! How", " are", " you", "?"]

    def _get_client(self):
        return self

    async def stream(self, messages, **kwargs):
        """Mock stream that can fail after N chunks."""
        self.call_count += 1

        for i, chunk in enumerate(self.chunks):
            if self.fail_after_chunks and i >= self.fail_after_chunks and self.call_count == 1:
                # Simulate rate limit on first call after N chunks
                raise Exception("Rate limit exceeded")
            yield chunk


@pytest.mark.asyncio
async def test_successful_no_retry():
    """Test normal streaming without any failures."""
    provider = StreamMockProvider()
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    async for chunk in provider.stream(messages):
        chunks.append(chunk)

    assert chunks == ["Hello", " there", "! How", " are", " you", "?"]
    assert provider.call_count == 1


@pytest.mark.asyncio
async def test_seamless_resumption():
    """Test stream retries seamlessly after rate limit."""
    provider = StreamMockProvider(fail_after_chunks=3)  # Fail after 3 chunks
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    with patch("cogency.providers.rotation.is_rate_limit", return_value=True):
        async for chunk in provider.stream(messages):
            chunks.append(chunk)

    # Should get all chunks despite the failure
    assert chunks == ["Hello", " there", "! How", " are", " you", "?"]

    # Should have retried (called twice due to rate limit)
    assert provider.call_count == 2


@pytest.mark.asyncio
async def test_buffer_replay():
    """Test that buffered chunks are replayed correctly."""
    provider = StreamMockProvider(fail_after_chunks=2)
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    chunk_sources = []  # Track which chunks come from buffer vs fresh stream

    with patch("cogency.providers.rotation.is_rate_limit", return_value=True):
        async for chunk in provider.stream(messages):
            chunks.append(chunk)
            # First 2 chunks on retry come from buffer, rest from fresh stream
            chunk_sources.append(
                "buffer" if len(chunks) <= 2 and provider.call_count > 1 else "fresh"
            )

    # All chunks delivered correctly
    assert chunks == ["Hello", " there", "! How", " are", " you", "?"]

    # Verify buffering worked (some chunks came from buffer)
    assert "buffer" in chunk_sources or provider.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhaustion():
    """Test stream fails when all keys exhausted."""
    provider = StreamMockProvider(api_keys=["single_key"], fail_after_chunks=2)
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    with patch("cogency.providers.rotation.is_rate_limit", return_value=True):
        with pytest.raises(KeyRotationError) as exc_info:
            async for chunk in provider.stream(messages):
                chunks.append(chunk)

    # Should get partial chunks before failure
    assert chunks == ["Hello", " there"]
    assert "no backup keys available" in str(exc_info.value)


@pytest.mark.asyncio
async def test_non_rate_limit_not_retried():
    """Test non-rate-limit errors aren't retried."""

    class FailingProvider(Provider):
        def __init__(self):
            rotator = setup_rotator("fail", ["key1", "key2"], required=True)
            super().__init__(rotator=rotator, model="fail-model")

        def _get_client(self):
            return self

        async def stream(self, messages, **kwargs):
            yield "chunk1"
            raise ValueError("Non-rate-limit error")

    provider = FailingProvider()
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    with pytest.raises(ValueError) as exc_info:
        async for chunk in provider.stream(messages):
            chunks.append(chunk)

    # Should get first chunk then fail
    assert chunks == ["chunk1"]
    assert "Non-rate-limit error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_without_rotator_no_retry():
    """Test streaming without rotator doesn't attempt retry."""

    class NoRotatorProvider(Provider):
        def __init__(self):
            super().__init__(rotator=None, model="no-rotator-model")

        def _get_client(self):
            return self

        async def stream(self, messages, **kwargs):
            yield "chunk1"
            raise Exception("Rate limit exceeded")

    provider = NoRotatorProvider()
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    with pytest.raises(Exception) as exc_info:
        async for chunk in provider.stream(messages):
            chunks.append(chunk)

    assert chunks == ["chunk1"]
    assert "Rate limit exceeded" in str(exc_info.value)


@pytest.mark.asyncio
async def test_preserves_method_signature():
    """Test stream retry decorator preserves method signatures."""
    provider = StreamMockProvider()

    # Check that functools.wraps preserved the signature
    stream_method = provider.__class__.stream
    assert hasattr(stream_method, "__wrapped__")
    assert stream_method.__name__ == "stream"
    assert callable(stream_method)

    # Verify the decorator marker
    assert getattr(stream_method, "_is_stream_retry", False)


@pytest.mark.asyncio
async def test_quota_exhaustion():
    """Test stream handles quota exhaustion differently from rate limits."""
    provider = StreamMockProvider(fail_after_chunks=2)
    messages = [{"role": "user", "content": "Hello"}]

    chunks = []
    with patch("cogency.providers.rotation.is_quota_exhausted", return_value=True):
        # Mock rotator to track removal calls
        original_remove = provider.rotator.remove_exhausted_key
        remove_called = False

        def mock_remove():
            nonlocal remove_called
            remove_called = True
            return original_remove()

        provider.rotator.remove_exhausted_key = mock_remove

        async for chunk in provider.stream(messages):
            chunks.append(chunk)

    # Should complete successfully and call remove_exhausted_key
    assert chunks == ["Hello", " there", "! How", " are", " you", "?"]
    assert remove_called
