"""Test token bucket rate limiting."""

import asyncio
import time

import pytest

from cogency.resilience.rate_limit import rate_limit


@pytest.mark.asyncio
async def test_rate_limit_enforces_rate():
    """Test rate limiting enforces requests per second."""

    @rate_limit(rps=50.0, burst=1)  # 50 RPS, 1 burst
    async def fast_function():
        return time.time()

    # Call function 3 times rapidly - after first, should be rate limited
    start = time.time()
    results = []
    for _ in range(3):
        result = await fast_function()
        results.append(result)

    elapsed = time.time() - start

    # Should take ~40ms for 3 calls: 1 immediate + 2 x 20ms waits
    assert elapsed >= 0.020, f"Rate limiting too loose: {elapsed}s"
    assert elapsed < 0.08, f"Rate limiting too strict: {elapsed}s"


@pytest.mark.asyncio
async def test_rate_limit_burst_allowance():
    """Test burst size allows initial rapid calls."""

    @rate_limit(rps=25.0, burst=3)  # 25 RPS, 3 burst
    async def burst_function():
        return time.time()

    # First 3 calls should be immediate (burst)
    start = time.time()
    results = []
    for _ in range(3):
        result = await burst_function()
        results.append(result)

    burst_time = time.time() - start
    assert burst_time < 0.01, f"Burst too slow: {burst_time}s"

    # 4th call should wait for rate limit
    fourth_start = time.time()
    await burst_function()
    fourth_time = time.time() - fourth_start

    assert fourth_time >= 0.035, f"Rate limit not enforced after burst: {fourth_time}s"


@pytest.mark.asyncio
async def test_rate_limit_per_function_isolation():
    """Test rate limiting isolates different functions."""

    @rate_limit(rps=50.0, burst=1)
    async def function_a():
        return "A"

    @rate_limit(rps=50.0, burst=1)
    async def function_b():
        return "B"

    # Call function_a twice - second call should be rate limited
    await function_a()
    start_a = time.time()
    await function_a()
    elapsed_a = time.time() - start_a

    # function_b should still be fast (separate rate limit)
    start_b = time.time()
    result_b = await function_b()
    elapsed_b = time.time() - start_b

    assert elapsed_a >= 0.015, f"Function A rate limit not enforced: {elapsed_a}s"
    assert elapsed_b < 0.005, f"Function B affected by A's rate limit: {elapsed_b}s"
    assert result_b == "B"


@pytest.mark.asyncio
async def test_rate_limit_custom_key():
    """Test custom key allows shared rate limiting."""

    @rate_limit(rps=50.0, burst=1, key="shared_limit")
    async def function_x():
        return "X"

    @rate_limit(rps=50.0, burst=1, key="shared_limit")
    async def function_y():
        return "Y"

    # Call function_x to consume shared tokens
    await function_x()
    start = time.time()

    # function_y should be rate limited (shares the same key)
    result = await function_y()
    elapsed = time.time() - start

    assert elapsed >= 0.015, f"Shared rate limit not enforced: {elapsed}s"
    assert result == "Y"
