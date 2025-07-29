"""Test LLM caching functionality."""

import pytest

from cogency.services import LLMCache


def test_creation():
    cache = LLMCache()
    assert cache.is_enabled()
    assert cache._max_size == 1000
    assert cache._ttl_seconds == 3600


def test_disabled():
    cache = LLMCache(max_size=0)
    assert not cache.is_enabled()


@pytest.mark.asyncio
async def test_miss():
    cache = LLMCache()
    messages = [{"role": "user", "content": "Hello"}]

    # Should be a miss initially
    result = await cache.get(messages)
    assert result is None

    # Set a value
    await cache.set(messages, "Test response")

    # Should be a hit now
    result = await cache.get(messages)
    assert result == "Test response"


@pytest.mark.asyncio
async def test_key_gen():
    cache = LLMCache()
    messages1 = [{"role": "user", "content": "Hello"}]
    messages2 = [{"role": "user", "content": "Hello"}]
    messages3 = [{"role": "user", "content": "Hi"}]

    key1 = cache._generate_key(messages1)
    key2 = cache._generate_key(messages2)
    key3 = cache._generate_key(messages3)

    assert key1 == key2  # Same content should have same key
    assert key1 != key3  # Different content should have different keys


@pytest.mark.asyncio
async def test_stats():
    cache = LLMCache()
    messages = [{"role": "user", "content": "Hello"}]

    # Initial stats
    stats = cache.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0

    # Miss
    await cache.get(messages)
    stats = cache.get_stats()
    assert stats["misses"] == 1

    # Set and hit
    await cache.set(messages, "Response")
    result = await cache.get(messages)
    assert result == "Response"

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["hit_rate"] == 0.5  # 1 hit out of 2 total requests


@pytest.mark.asyncio
async def test_clear():
    cache = LLMCache()
    messages = [{"role": "user", "content": "Hello"}]

    await cache.set(messages, "Response")
    assert await cache.get(messages) == "Response"

    await cache.clear()
    assert await cache.get(messages) is None
