"""Test LLM caching functionality."""

import pytest

from cogency.services.llm.cache import LLMCache, cached_llm_call, configure_cache, get_cache


def test_creation():
    cache = LLMCache()
    assert cache.is_enabled()
    assert cache._max_size == 1000
    assert cache._ttl_seconds == 3600


def test_disabled():
    cache = LLMCache(max_size=0)
    assert not cache.is_enabled()


@pytest.mark.asyncio
async def test_miss_and_set():
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
async def test_key_generation():
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


@pytest.mark.asyncio
async def test_cached_call():
    call_count = 0

    async def mock_llm_func(messages, **kwargs):
        nonlocal call_count
        call_count += 1
        return f"Response {call_count}"

    messages = [{"role": "user", "content": "Hello"}]

    # Clear cache first
    cache = get_cache()
    await cache.clear()

    # First call should execute function
    result1 = await cached_llm_call(mock_llm_func, messages)
    assert result1 == "Response 1"
    assert call_count == 1

    # Second call should use cache
    result2 = await cached_llm_call(mock_llm_func, messages)
    assert result2 == "Response 1"  # Same as first call
    assert call_count == 1  # Function not called again

    # Different messages should execute function
    different_messages = [{"role": "user", "content": "Hi"}]
    result3 = await cached_llm_call(mock_llm_func, different_messages)
    assert result3 == "Response 2"
    assert call_count == 2


@pytest.mark.asyncio
async def test_cached_call_disabled():
    call_count = 0

    async def mock_llm_func(messages, **kwargs):
        nonlocal call_count
        call_count += 1
        return f"Response {call_count}"

    messages = [{"role": "user", "content": "Hello"}]

    # Call with caching disabled
    result1 = await cached_llm_call(mock_llm_func, messages, use_cache=False)
    assert result1 == "Response 1"
    assert call_count == 1

    # Second call should also execute function
    result2 = await cached_llm_call(mock_llm_func, messages, use_cache=False)
    assert result2 == "Response 2"
    assert call_count == 2


def test_global_configuration():
    # Configure with custom settings
    configure_cache(max_size=500, ttl_seconds=1800)

    cache = get_cache()
    assert cache._max_size == 500
    assert cache._ttl_seconds == 1800
