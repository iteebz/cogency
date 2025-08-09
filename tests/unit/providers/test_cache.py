"""Provider cache unit tests."""

import pytest

from cogency.providers import Cache


@pytest.mark.asyncio
async def test_cache_basic_operations():
    """Test basic cache set/get/clear operations."""
    cache = Cache()
    await cache.clear()

    # Test set and get
    input_data = {"messages": [{"role": "user", "content": "test"}]}
    response = "test response"

    await cache.set(input_data, response)
    cached = await cache.get(input_data)

    assert cached is not None
    assert cached == response


@pytest.mark.asyncio
async def test_cache_stats():
    """Test cache statistics tracking."""
    cache = Cache()
    await cache.clear()

    # Initially no hits or misses
    stats = cache.get_stats()
    assert stats["hits"] == 0
    assert stats["misses"] == 0
    assert stats["hit_rate"] == 0.0

    input_data = {"test": "data"}

    # Miss
    result = await cache.get(input_data)
    assert result is None
    stats = cache.get_stats()
    assert stats["misses"] == 1
    assert stats["hits"] == 0

    # Set and hit
    await cache.set(input_data, "response")
    result = await cache.get(input_data)
    assert result is not None
    stats = cache.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["hit_rate"] == 0.5


@pytest.mark.asyncio
async def test_cache_different_keys():
    """Test that different input data creates different cache entries."""
    cache = Cache()
    await cache.clear()

    input1 = {"test": "data1"}
    input2 = {"test": "data2"}

    await cache.set(input1, "response1")
    await cache.set(input2, "response2")

    result1 = await cache.get(input1)
    result2 = await cache.get(input2)

    assert result1 == "response1"
    assert result2 == "response2"


@pytest.mark.asyncio
async def test_cache_clear():
    """Test cache clearing functionality."""
    cache = Cache()

    # Add some data
    await cache.set({"test": "data"}, "response")
    result = await cache.get({"test": "data"})
    assert result is not None

    # Clear and verify empty
    await cache.clear()
    result = await cache.get({"test": "data"})
    assert result is None
