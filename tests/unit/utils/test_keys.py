"""Test LLM key rotation and LLM integration."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency.providers import Provider
from cogency.utils.keys import KeyManager, KeyRotationError, KeyRotator
from tests.conftest import mock_provider


def test_provider(mock_provider):
    # Single key
    mock_provider.keys = KeyManager(api_key="single_key")
    assert mock_provider.keys.current == "single_key"
    assert not mock_provider.keys.has_multiple()

    # Multiple keys
    keys = ["key1", "key2", "key3"]
    mock_provider.keys = KeyManager.for_provider("test", keys)
    assert mock_provider.keys.has_multiple()
    assert mock_provider.next_key() in keys


@pytest.mark.asyncio
async def test_methods(mock_provider):
    mock_provider.response = "Mock response"
    messages = [{"role": "user", "content": "Hello"}]

    # Test run method
    result = await mock_provider.run(messages)
    assert result.success
    assert isinstance(result.data, str)
    assert len(result.data) > 0

    # Test stream method
    chunks = []
    async for chunk in mock_provider.stream(messages):
        chunks.append(chunk)
        assert isinstance(chunk, str)
    assert len(chunks) > 0


def test_rotation(mock_provider):
    keys = ["key1", "key2", "key3"]
    mock_provider.keys = KeyManager.for_provider("test", keys)

    # Track keys used across multiple calls
    used_keys = []
    for _ in range(6):  # More than number of keys to see cycling
        used_keys.append(mock_provider.next_key())

    # Should have rotated through all keys
    unique_keys = set(used_keys)
    assert len(unique_keys) == 3


def test_rotator():
    # Single key
    rotator = KeyRotator(["key1"])
    assert rotator.current_key == "key1"
    assert rotator.get_next_key() == "key1"

    # Multiple keys
    keys = ["key1", "key2", "key3"]
    rotator = KeyRotator(keys)
    first_key = rotator.current_key
    assert first_key in keys

    # Should cycle through all keys
    seen_keys = {first_key}
    for _ in range(10):  # More cycles than keys
        seen_keys.add(rotator.get_next_key())
    assert seen_keys == set(keys)


def test_manager():
    # Single key
    manager = KeyManager(api_key="single_key")
    assert manager.current == "single_key"
    assert not manager.has_multiple()

    # Multiple keys
    keys = ["key1", "key2", "key3"]
    manager = KeyManager.for_provider("test", keys)
    assert manager.has_multiple()
    assert manager.current in keys
    assert manager.get_next() in keys


@patch.dict(
    "os.environ",
    {"TEST_API_KEY_1": "key1", "TEST_API_KEY_2": "key2", "TEST_API_KEY_3": "key3"},
)
def test_numbered():
    manager = KeyManager.for_provider("test")
    assert manager.has_multiple()
    assert len(manager.key_rotator.keys) == 3


@patch.dict("os.environ", {"TEST_API_KEY": "single_key"})
def test_single():
    manager = KeyManager.for_provider("test")
    assert not manager.has_multiple()
    assert manager.current == "single_key"


@patch.dict("os.environ", {}, clear=True)
def test_none():
    with pytest.raises(Exception):
        KeyManager.for_provider("test")


@pytest.mark.asyncio
async def test_retry_success():
    manager = KeyManager.for_provider("test", ["key1", "key2"])

    mock_func = AsyncMock(return_value="success")
    result = await manager.retry_rate_limit(mock_func, "arg1", kwarg1="value1")

    assert result == "success"
    mock_func.assert_called_once_with("arg1", kwarg1="value1")


@pytest.mark.asyncio
async def test_retry_non_rate_limit():
    manager = KeyManager.for_provider("test", ["key1", "key2"])

    mock_func = AsyncMock(side_effect=ValueError("some other error"))

    with pytest.raises(ValueError, match="some other error"):
        await manager.retry_rate_limit(mock_func)


@pytest.mark.asyncio
async def test_retry_single_key():
    manager = KeyManager(api_key="single_key")

    mock_func = AsyncMock(side_effect=Exception("rate limit exceeded"))

    with pytest.raises(KeyRotationError, match="All API keys exhausted"):
        await manager.retry_rate_limit(mock_func)


@pytest.mark.asyncio
async def test_retry_rotation_success():
    manager = KeyManager.for_provider("test", ["key1", "key2"])

    # First call fails with rate limit, second succeeds
    mock_func = AsyncMock(side_effect=[Exception("429 too many requests"), "success"])

    result = await manager.retry_rate_limit(mock_func)

    assert result == "success"
    assert mock_func.call_count == 2


@pytest.mark.asyncio
async def test_retry_exhausted():
    manager = KeyManager.for_provider("test", ["key1", "key2"])

    # First fails with rate limit, second with quota (removes key), third fails with rate limit on last key
    mock_func = AsyncMock(
        side_effect=[
            Exception("rate limit exceeded"),
            Exception("quota exceeded"),
            Exception("rate limit exceeded"),
        ]
    )

    with pytest.raises(KeyRotationError, match="All API keys exhausted"):
        await manager.retry_rate_limit(mock_func)

    assert mock_func.call_count == 3


@pytest.mark.asyncio
async def test_retry_different_error():
    manager = KeyManager.for_provider("test", ["key1", "key2"])

    # First call rate limited, second has different error
    mock_func = AsyncMock(side_effect=[Exception("429 rate limit"), ValueError("validation error")])

    with pytest.raises(ValueError, match="validation error"):
        await manager.retry_rate_limit(mock_func)
