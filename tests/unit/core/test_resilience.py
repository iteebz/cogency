import pytest
import asyncio
from cogency.core.resilience import RateLimiter, CircuitBreaker, with_retry, RateLimiterConfig, CircuitBreakerConfig, CircuitOpenError

@pytest.fixture
def rate_limiter():
    return RateLimiter(RateLimiterConfig(requests_per_minute=60, burst_size=2))

@pytest.fixture
def circuit_breaker():
    return CircuitBreaker("test_breaker", CircuitBreakerConfig(failure_threshold=2, recovery_timeout=10))

@pytest.mark.asyncio
async def test_rate_limiter_allows_requests(rate_limiter):
    """Test that the rate limiter allows requests within the limit."""
    assert await rate_limiter.acquire() is True
    assert await rate_limiter.acquire() is True
    assert await rate_limiter.acquire() is False

@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures(circuit_breaker):
    """Test that the circuit breaker opens after enough failures."""
    async def failing_function():
        raise ValueError("failure")

    with pytest.raises(ValueError):
        await circuit_breaker.call(failing_function)
    with pytest.raises(ValueError):
        await circuit_breaker.call(failing_function)

    with pytest.raises(CircuitOpenError):
        await circuit_breaker.call(failing_function)

@pytest.mark.asyncio
async def test_with_retry_succeeds_after_failures():
    """Test that the with_retry decorator succeeds after a few failures."""
    attempts = 0

    @with_retry(max_attempts=3, base_delay=0.01)
    async def flaky_function():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("temporary failure")
        return "success"

    result = await flaky_function()
    assert result == "success"
    assert attempts == 3

@pytest.mark.asyncio
async def test_with_retry_fails_after_max_attempts():
    """Test that the with_retry decorator fails after all attempts are exhausted."""
    @with_retry(max_attempts=3, base_delay=0.01)
    async def failing_function():
        raise ValueError("permanent failure")

    with pytest.raises(ValueError):
        await failing_function()