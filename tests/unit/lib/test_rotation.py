import os
from unittest.mock import patch

import pytest

from cogency.lib.rotation import Rotator, _rotators, rotate, with_rotation


def setup_function():
    _rotators.clear()


@pytest.mark.asyncio
async def test_api_key_rotation_behavior():
    """Core rotation behavior: auto-balance, rate limit detection, retry with exhaustion."""

    # Basic rotation mechanics
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        rotator = Rotator("test")
        assert rotator.keys == ["key1", "key2"]
        assert rotator.current_key() == "key1"

        # Rate limit detection triggers rotation
        with patch("cogency.lib.rotation.time.time", side_effect=range(10)):
            assert rotator.rotate("Rate limit exceeded") is True
            assert rotator.rotate("quota exceeded") is True
            assert rotator.rotate("invalid key") is False  # Non-rate-limit error

        # Auto-balancing through with_rotation
        call_keys = []

        async def capture_key(api_key):
            call_keys.append(api_key)
            return f"response_{api_key}"

        # Multiple calls auto-rotate for load balancing
        for _ in range(4):
            result = await with_rotation("TEST", capture_key)
            assert result.success

        # Should alternate keys: key1→key2, key2→key1, etc.
        assert call_keys == ["key2", "key1", "key2", "key1"]

        # Quota exhaustion and retry behavior
        call_count = 0

        async def quota_test(api_key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("You exceeded your current quota")
            return "success_after_retry"

        result = await with_rotation("TEST", quota_test)
        assert result.success
        assert call_count == 2  # Auto-rotate + retry

        # All keys exhausted scenario
        async def all_exhausted(api_key):
            raise Exception("received 1011 (internal error) You exceeded your current quota")

        result = await with_rotation("TEST", all_exhausted)
        assert not result.success
        assert "quota" in result.error.lower()

    # @rotate decorator auto-detection and fresh clients
    class MockProvider:
        def _create_client(self, api_key):
            return f"client_{api_key}"

        @rotate
        async def method(self, client, data):
            if "fail_key" in client:
                raise Exception("rate limit exceeded")
            return f"result_{client}_{data}"

    # Auto-detects MOCKPROVIDER prefix, handles missing keys
    provider = MockProvider()
    result = await provider.method("test")
    assert result.failure
    assert "No MOCKPROVIDER API keys found" in result.error

    # Creates fresh clients and rotates on rate limits
    with patch.dict(
        os.environ,
        {"MOCKPROVIDER_API_KEY": "fail_key", "MOCKPROVIDER_API_KEY_2": "good_key"},
        clear=True,
    ):
        _rotators.clear()
        result = await provider.method("data")
        assert result.success
        assert "good_key" in result.unwrap()  # Rotated from fail_key to good_key
