"""LLM caching integration tests."""

import pytest

from cogency.providers import LLMCache
from tests.fixtures.llm import MockLLM


@pytest.mark.asyncio
async def test_caching():
    """Test that LLM caching works in practice."""
    # Create fresh cache for this test
    cache = LLMCache()
    await cache.clear()

    # Create LLM with caching enabled
    llm = MockLLM(response="Cached response", enable_cache=True)
    llm._cache = cache  # Use our test cache instance
    messages = [{"role": "user", "content": "Test caching"}]

    # First call should execute and cache
    result1 = await llm.run(messages)
    assert result1.success
    assert result1.data == "Cached response"

    # Check cache stats
    stats = cache.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0

    # Second call should use cache
    result2 = await llm.run(messages)
    assert result2.success
    assert result2.data == "Cached response"

    # Check cache stats again
    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5


@pytest.mark.asyncio
async def test_disabled():
    """Test LLM with caching disabled."""
    # Create fresh cache for this test
    cache = LLMCache()
    await cache.clear()

    # Create LLM with caching disabled
    llm = MockLLM(response="Not cached", enable_cache=False)
    messages = [{"role": "user", "content": "Test no caching"}]

    # Multiple calls should not affect cache
    result1 = await llm.run(messages)
    assert result1.success
    result2 = await llm.run(messages)
    assert result2.success

    # Cache should show no activity
    stats = cache.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0


@pytest.mark.asyncio
async def test_different_messages():
    """Test that different messages create different cache entries."""
    # Create fresh cache for this test
    cache = LLMCache()
    await cache.clear()

    llm = MockLLM(enable_cache=True)
    llm._cache = cache  # Use our test cache instance

    # Two different messages
    messages1 = [{"role": "user", "content": "First message"}]
    messages2 = [{"role": "user", "content": "Second message"}]

    # Call with first message
    result1 = await llm.run(messages1)
    assert result1.success

    # Call with second message
    result2 = await llm.run(messages2)
    assert result2.success

    # Both should be cache misses
    stats = cache.get_stats()
    assert stats["misses"] == 2
    assert stats["hits"] == 0

    # Call first message again - should be cache hit
    await llm.run(messages1)

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 2
