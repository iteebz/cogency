import os
from unittest.mock import patch

import pytest

from cogency.lib.llms.rotation import get_api_key, is_rate_limit_error, load_keys, with_rotation


def test_load_keys():
    """Tests key loading with numbered and single patterns."""
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        keys = load_keys("TEST")
        assert keys == ["key1", "key2"]


def test_get_api_key():
    """Tests basic key retrieval and service alias support."""
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1"}, clear=True):
        assert get_api_key("test") == "key1"

    with patch.dict(os.environ, {"GOOGLE_API_KEY": "google_key"}, clear=True):
        assert get_api_key("gemini") == "google_key"


def test_is_rate_limit_error():
    """Tests the rate limit error detection logic."""
    assert is_rate_limit_error("Rate limit exceeded") is True
    assert is_rate_limit_error("quota exceeded") is True
    assert is_rate_limit_error("API key exhausted") is True
    assert is_rate_limit_error("invalid key") is False
    assert is_rate_limit_error("An unknown error occurred") is False


@pytest.mark.asyncio
async def test_cycles_keys():
    """Tests that with_rotation cycles through the available keys."""
    call_keys = []

    async def capture_key(api_key):
        call_keys.append(api_key)
        return f"response_{api_key}"

    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        with patch("random.randint") as mock_randint:
            mock_randint.side_effect = [0, 1, 0, 1]  # Ensure predictable cycling
            for _ in range(4):
                await with_rotation("TEST", capture_key)

        assert "key1" in call_keys
        assert "key2" in call_keys
        # With predictable randint, we can check for exact cycling
        assert call_keys == ["key1", "key2", "key1", "key2"]


@pytest.mark.asyncio
async def test_retries_on_rate_limit():
    """Tests that with_rotation retries with the next key upon a rate limit error."""
    call_count = 0

    async def quota_test(api_key):
        nonlocal call_count
        call_count += 1
        if api_key == "key1":
            raise Exception("You exceeded your current quota")
        return "success_after_retry"

    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        with patch("random.randint") as mock_randint:
            mock_randint.return_value = 0
            result = await with_rotation("TEST", quota_test)
            assert result == "success_after_retry"
            assert call_count == 2  # First key fails, second succeeds


@pytest.mark.asyncio
async def test_fails_when_all_keys_exhausted():
    """Tests that with_rotation raises the last error when all keys are exhausted."""

    async def all_exhausted(api_key):
        raise Exception(f"Quota exceeded for {api_key}")

    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        with pytest.raises(Exception) as exc_info:
            await with_rotation("TEST", all_exhausted)
        # The final exception (from the last key tried) should be raised
        assert "Quota exceeded for" in str(exc_info.value)
