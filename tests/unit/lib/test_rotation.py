
import os
from unittest.mock import patch

import pytest

from cogency.lib.rotation import get_api_key, is_rate_limit_error, load_keys, with_rotation


@pytest.mark.asyncio
async def test_rotation():

    # Key loading with numbered and single patterns
    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        keys = load_keys("TEST")
        assert keys == ["key1", "key2"]

        # get_api_key returns first key
        assert get_api_key("test") == "key1"

    # Service alias support
    with patch.dict(os.environ, {"GOOGLE_API_KEY": "google_key"}, clear=True):
        assert get_api_key("gemini") == "google_key"

    # Rate limit detection
    assert is_rate_limit_error("Rate limit exceeded") is True
    assert is_rate_limit_error("quota exceeded") is True
    assert is_rate_limit_error("invalid key") is False

    # Rotation with multiple keys
    call_keys = []

    async def capture_key(api_key):
        call_keys.append(api_key)
        return f"response_{api_key}"

    with patch.dict(os.environ, {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2"}, clear=True):
        # Multiple calls should use random starting positions
        with patch("random.randint") as mock_randint:
            mock_randint.side_effect = [0, 1] * 5
            for _ in range(10):
                result = await with_rotation("TEST", capture_key)
                assert result.startswith("response_")

        # Should see both keys used (random distribution)
        assert "key1" in call_keys
        assert "key2" in call_keys

        # Retry on rate limit
        call_count = 0

        async def quota_test(api_key):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("You exceeded your current quota")
            return "success_after_retry"

        call_count = 0
        result = await with_rotation("TEST", quota_test)
        assert result == "success_after_retry"
        assert call_count == 2  # First fails, second succeeds

        # All keys exhausted
        async def all_exhausted(api_key):
            raise Exception("received 1011 (internal error) You exceeded your current quota")

        with pytest.raises(Exception) as exc_info:
            await with_rotation("TEST", all_exhausted)
        assert "quota" in str(exc_info.value).lower()
