"""Canonical rotation tests - comprehensive coverage."""

import os
from unittest.mock import patch

import pytest

from cogency.lib.rotation import Rotator, _rotators, rotate, with_rotation


def setup_function():
    """Clear global state."""
    _rotators.clear()


def test_rotation_basics():
    """Test core rotation functionality."""
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        rotator = Rotator("test")

        # Keys loaded correctly
        assert rotator.keys == ["key1", "key2"]
        assert rotator.current_key() == "key1"

        # Rotation works on rate limits
        with patch("cogency.lib.rotation.time.time", side_effect=[2, 4]):
            assert rotator.rotate("Rate limit exceeded") is True
            assert rotator.current_key() == "key2"


def test_rate_limit_detection():
    """Test rate limit signal detection."""
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        rotator = Rotator("test")

        # Rate limit signals trigger rotation (with time progression)
        with patch("cogency.lib.rotation.time.time", side_effect=[2, 4, 6]):
            assert rotator.rotate("quota exceeded") is True
            assert rotator.rotate("429 error") is True
            assert rotator.rotate("throttle limit") is True

        # Non-rate-limit errors don't trigger rotation
        assert rotator.rotate("invalid key") is False
        assert rotator.rotate("connection error") is False


@pytest.mark.asyncio
async def test_wrapper_function():
    """Test with_rotation wrapper with automatic rotation."""
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):

        async def mock_api(api_key):
            # First call gets rotated to key2 (auto-rotation from key1)
            assert api_key == "key2"
            return "success"

        result = await with_rotation("TEST", mock_api)
        assert result.success
        assert result.unwrap() == "success"


@pytest.mark.asyncio
async def test_provider_integration():
    """Test real provider pattern with single key (no rotation)."""
    with patch.dict(os.environ, {"GEMINI_API_KEY": "real_key"}, clear=True):

        async def _generate(api_key):
            assert api_key == "real_key"
            return "Generated text"

        result = await with_rotation("GEMINI", _generate)
        assert result.success
        assert result.unwrap() == "Generated text"


@pytest.mark.asyncio
async def test_websocket_quota_rotation():
    """Test automatic rotation + retry on WebSocket quota errors."""
    with patch.dict(
        os.environ, {"GEMINI_API_KEY_1": "key1", "GEMINI_API_KEY_2": "key2"}, clear=True
    ):
        call_count = 0

        # Mock time progression for rotations
        with patch("cogency.lib.rotation.time.time", side_effect=[0, 1, 2, 3, 4, 5, 6]):

            async def _websocket_connect(api_key):
                nonlocal call_count
                call_count += 1

                if call_count == 1:
                    # First call: auto-rotated to key2, but it hits quota
                    assert api_key == "key2"
                    raise Exception(
                        "You exceeded your current quota, please check your plan and billing details"
                    )
                if call_count == 2:
                    # Retry call: rotated to key1, succeeds
                    assert api_key == "key1"
                    return {"session": "mock_session", "connection": "mock_conn"}
                return None

            result = await with_rotation("GEMINI", _websocket_connect)
            assert result.success
            assert call_count == 2  # Auto-rotate + retry = 2 calls


@pytest.mark.asyncio
async def test_websocket_all_keys_exhausted():
    """Test behavior when all keys hit quota limits."""
    with patch.dict(
        os.environ, {"GEMINI_API_KEY_1": "key1", "GEMINI_API_KEY_2": "key2"}, clear=True
    ):
        call_count = 0

        # Mock time progression for rotations
        with patch("cogency.lib.rotation.time.time", side_effect=[0, 1, 2, 3, 4, 5, 6]):

            async def _websocket_connect(api_key):
                nonlocal call_count
                call_count += 1
                # Both keys hit quota (first auto-rotated call + retry)
                raise Exception("received 1011 (internal error) You exceeded your current quota")

            result = await with_rotation("GEMINI", _websocket_connect)
            assert not result.success
            assert "quota" in result.error.lower()
            assert call_count == 2  # Auto-rotate + retry, both fail


@pytest.mark.asyncio
async def test_automatic_load_balancing():
    """Test that every call automatically rotates keys for load balancing."""
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        call_results = []

        # Mock time to allow rapid rotations
        with patch("cogency.lib.rotation.time.time", side_effect=range(1, 20)):

            async def _api_call(api_key):
                call_results.append(api_key)
                return f"response_from_{api_key}"

            # Make 4 consecutive calls - should auto-rotate through keys
            for _i in range(4):
                result = await with_rotation("TEST", _api_call)
                assert result.success

            # Debug what we actually got
            print(f"Actual calls: {call_results}")

            # Now with proper rotation, should get perfect alternation
            # Each call auto-rotates: key1->key2, key2->key1, key1->key2, key2->key1
            expected = ["key2", "key1", "key2", "key1"]
            assert call_results == expected


class MockProvider:
    """Mock provider for decorator testing."""

    def _create_client(self, api_key):
        return f"client_{api_key}"

    @rotate
    async def method(self, client, data):
        return f"result_{client}_{data}"


@pytest.mark.asyncio
async def test_rotate_decorator_auto_prefix():
    """Auto-detects provider prefix from class name."""
    provider = MockProvider()

    result = await provider.method("test")
    assert result.failure
    assert "No MOCKPROVIDER API keys found" in result.error


@pytest.mark.asyncio
async def test_rotate_decorator_fresh_clients():
    """Creates fresh clients for each call (no caching)."""
    with patch.dict(os.environ, {"MOCKPROVIDER_API_KEY": "key123"}, clear=True):
        _rotators.clear()

        provider = MockProvider()

        # First call creates client
        result = await provider.method("data1")
        assert result.success
        assert result.unwrap() == "result_client_key123_data1"

        # Second call creates fresh client
        result = await provider.method("data2")
        assert result.success
        assert result.unwrap() == "result_client_key123_data2"


@pytest.mark.asyncio
async def test_rotate_decorator_rotation():
    """Rotates keys on rate limit errors."""

    class FailProvider:
        def _create_client(self, api_key):
            return f"client_{api_key}"

        @rotate
        async def method(self, client, data):
            if "key1" in client:
                raise Exception("rate limit exceeded")
            return f"success_{client}"

    with patch.dict(
        os.environ, {"FAILPROVIDER_API_KEY": "key1", "FAILPROVIDER_API_KEY_2": "key2"}, clear=True
    ):
        _rotators.clear()

        provider = FailProvider()

        # Should rotate from key1 to key2
        result = await provider.method("test")
        assert result.success
        assert result.unwrap() == "success_client_key2"
