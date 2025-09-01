"""Rotation core logic tests."""

import pytest

from cogency.lib.rotation import _client_cache, rotate


class MockProvider:
    def _create_client(self, api_key):
        return f"client_{api_key}"

    @rotate
    async def method(self, client, data):
        return f"result_{client}_{data}"


@pytest.mark.asyncio
async def test_auto_prefix():
    """Auto-detects provider prefix from class name."""
    provider = MockProvider()

    try:
        await provider.method("test")
    except ValueError as e:
        assert "No MOCKPROVIDER API keys found" in str(e)


@pytest.mark.asyncio
async def test_client_cache():
    """Caches clients per API key."""
    import os

    os.environ["MOCKPROVIDER_API_KEY"] = "key123"

    # Reset rotators to pick up new env var
    from cogency.lib.rotation import _rotators

    _rotators.clear()

    provider = MockProvider()

    # Clear cache
    _client_cache.clear()

    # First call creates client
    result = await provider.method("data1")
    assert result == "result_client_key123_data1"
    assert "MOCKPROVIDER:key123" in _client_cache

    # Second call uses cached client
    result = await provider.method("data2")
    assert result == "result_client_key123_data2"

    # Only one client created
    assert len(_client_cache) == 1

    # Cleanup
    del os.environ["MOCKPROVIDER_API_KEY"]
    _client_cache.clear()
    _rotators.clear()


@pytest.mark.asyncio
async def test_rotation():
    """Rotates keys on rate limit errors."""
    import os

    os.environ["FAILPROVIDER_API_KEY"] = "key1"
    os.environ["FAILPROVIDER_API_KEY_2"] = "key2"

    # Reset rotators to pick up new env vars
    from cogency.lib.rotation import _rotators

    _rotators.clear()

    class FailProvider:
        def _create_client(self, api_key):
            return f"client_{api_key}"

        @rotate
        async def method(self, client, data):
            if "key1" in client:
                raise Exception("rate limit exceeded")
            return f"success_{client}"

    provider = FailProvider()
    _client_cache.clear()

    # Should rotate from key1 to key2
    result = await provider.method("test")
    assert result == "success_client_key2"

    # Cleanup
    del os.environ["FAILPROVIDER_API_KEY"]
    del os.environ["FAILPROVIDER_API_KEY_2"]
    _client_cache.clear()
    _rotators.clear()
