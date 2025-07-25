"""LLM caching integration tests."""

import pytest

from cogency.types.cache import configure_cache, get_cache
from tests.conftest import MockLLM


@pytest.mark.asyncio
async def test_llm_caching_integration():
    """LLM caching works in practice."""
    configure_cache()
    cache = get_cache()
    await cache.clear()

    llm = MockLLM(response="Cached response", enable_cache=True)
    messages = [{"role": "user", "content": "Test caching"}]

    result1 = await llm.run(messages)
    assert result1.success
    assert result1.data == "Cached response"

    stats = cache.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0

    result2 = await llm.run(messages)
    assert result2.success

    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["hit_rate"] == 0.5


@pytest.mark.asyncio
async def test_llm_caching_disabled():
    """LLM with caching disabled."""
    configure_cache()
    cache = get_cache()
    await cache.clear()

    llm = MockLLM(response="Not cached", enable_cache=False)
    messages = [{"role": "user", "content": "Test no caching"}]

    await llm.run(messages)
    await llm.run(messages)

    stats = cache.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0


@pytest.mark.asyncio
async def test_different_messages_different_cache():
    """Different messages create different cache entries."""
    configure_cache()
    cache = get_cache()
    await cache.clear()

    llm = MockLLM(enable_cache=True)
    messages1 = [{"role": "user", "content": "First message"}]
    messages2 = [{"role": "user", "content": "Second message"}]

    await llm.run(messages1)
    await llm.run(messages2)

    stats = cache.get_stats()
    assert stats["misses"] == 2
    assert stats["hits"] == 0

    await llm.run(messages1)

    stats = cache.get_stats()
    assert stats["hits"] == 1
