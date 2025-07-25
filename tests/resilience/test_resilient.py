"""Test the magical @resilient decorator."""

import asyncio
import time

import pytest

from cogency.resilience.resilient import resilient


@pytest.mark.asyncio
async def test_resilient_rate_limit_only():
    """Test @resilient with rate limiting only."""

    @resilient(rps=50.0, burst=1)
    async def rate_limited_func():
        return time.time()

    # Should be rate limited after first call
    await rate_limited_func()
    start = time.time()
    await rate_limited_func()
    elapsed = time.time() - start

    assert elapsed >= 0.015, f"Rate limiting not working: {elapsed}s"


@pytest.mark.asyncio
async def test_resilient_circuit_only():
    """Test @resilient with circuit breaker only."""

    @resilient(failures=2, window=60)
    async def failing_func():
        raise Exception("Always fails")

    # Should work for 2 failures, then circuit opens
    for _ in range(2):
        with pytest.raises(Exception, match="Always fails"):
            await failing_func()

    # Third call should return circuit breaker message
    result = await failing_func()
    assert "Circuit breaker open" in result


@pytest.mark.asyncio
async def test_resilient_combined():
    """Test @resilient with both rate limiting and circuit breaking."""

    @resilient(rps=50.0, burst=1, failures=2, window=60)
    async def combined_func():
        if not hasattr(combined_func, "call_count"):
            combined_func.call_count = 0
        combined_func.call_count += 1

        if combined_func.call_count <= 2:
            raise Exception("Failing calls")
        return "success"

    # First call immediate (burst), second rate limited, both fail
    with pytest.raises(Exception, match="Failing calls"):
        await combined_func()

    start = time.time()
    with pytest.raises(Exception, match="Failing calls"):
        await combined_func()
    elapsed = time.time() - start

    # Should have been rate limited (20ms wait for 50 RPS)
    assert elapsed >= 0.015, f"Rate limiting not working: {elapsed}s"

    # Third call should hit circuit breaker
    result = await combined_func()
    assert "Circuit breaker open" in result


@pytest.mark.asyncio
async def test_resilient_no_config():
    """Test @resilient with no configuration (should pass through)."""

    @resilient()
    async def normal_func():
        return "works"

    result = await normal_func()
    assert result == "works"
