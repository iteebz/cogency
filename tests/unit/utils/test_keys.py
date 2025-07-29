"""Test LLM key rotation and LLM integration."""

from unittest.mock import patch

import pytest

from cogency.services.llm import LLM
from cogency.utils.keys import KeyManager, KeyRotator
from tests.conftest import MockLLM


def test_llm():
    # Single key
    llm = MockLLM(api_keys="single_key")
    assert llm.keys.get_current() == "single_key"
    assert not llm.keys.has_multiple()

    # Multiple keys
    keys = ["key1", "key2", "key3"]
    llm = MockLLM(api_keys=keys)
    assert llm.keys.has_multiple()
    assert llm.next_key() in keys


@pytest.mark.asyncio
async def test_methods():
    llm = MockLLM()
    messages = [{"role": "user", "content": "Hello"}]

    # Test run method
    result = await llm.run(messages)
    assert result.success
    assert isinstance(result.data, str)
    assert len(result.data) > 0

    # Test stream method
    chunks = []
    async for chunk in llm.stream(messages):
        chunks.append(chunk)
        assert isinstance(chunk, str)
    assert len(chunks) > 0


def test_rotation():
    keys = ["key1", "key2", "key3"]
    llm = MockLLM(api_keys=keys)

    # Track keys used across multiple calls
    used_keys = []
    for _ in range(6):  # More than number of keys to see cycling
        used_keys.append(llm.next_key())

    # Should have rotated through all keys
    unique_keys = set(used_keys)
    assert len(unique_keys) == 3


def test_rotator():
    # Single key
    rotator = KeyRotator(["key1"])
    assert rotator.get_current_key() == "key1"
    assert rotator.get_next_key() == "key1"

    # Multiple keys
    keys = ["key1", "key2", "key3"]
    rotator = KeyRotator(keys)
    first_key = rotator.get_current_key()
    assert first_key in keys

    # Should cycle through all keys
    seen_keys = {first_key}
    for _ in range(10):  # More cycles than keys
        seen_keys.add(rotator.get_next_key())
    assert seen_keys == set(keys)


def test_manager():
    # Single key
    manager = KeyManager(api_key="single_key")
    assert manager.get_current() == "single_key"
    assert not manager.has_multiple()

    # Multiple keys
    keys = ["key1", "key2", "key3"]
    manager = KeyManager.for_provider("test", keys)
    assert manager.has_multiple()
    assert manager.get_current() in keys
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
    assert manager.get_current() == "single_key"


@patch.dict("os.environ", {}, clear=True)
def test_none():
    with pytest.raises(Exception):
        KeyManager.for_provider("test")
