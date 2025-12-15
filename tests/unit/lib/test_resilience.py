"""Unit tests for cogency/lib/resilience.py."""

import pytest

from cogency.lib.resilience import CircuitBreaker, retry


@pytest.mark.asyncio
async def test_retry_immediate_success():
    """Returns result on first attempt without delay."""
    calls = 0

    @retry(attempts=3, base_delay=0.01)
    async def fn():
        nonlocal calls
        calls += 1
        return "done"

    assert await fn() == "done"
    assert calls == 1


@pytest.mark.asyncio
async def test_retry_succeeds_after_transients():
    """Retries on exception, succeeds when succeeds."""
    calls = 0

    @retry(attempts=3, base_delay=0.01)
    async def fn():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("transient")
        return "ok"

    assert await fn() == "ok"
    assert calls == 3


@pytest.mark.asyncio
async def test_retry_raises_after_exhaustion():
    """Raises original exception after all attempts fail."""
    calls = 0

    @retry(attempts=3, base_delay=0.01)
    async def fn():
        nonlocal calls
        calls += 1
        raise ValueError("persistent")

    with pytest.raises(ValueError, match="persistent"):
        await fn()
    assert calls == 3


@pytest.mark.asyncio
async def test_retry_exponential_backoff():
    """Waits longer between retries (2^attempt * base_delay)."""
    import time

    times = []

    @retry(attempts=3, base_delay=0.05)
    async def fn():
        times.append(time.time())
        if len(times) < 3:
            raise ValueError()
        return "ok"

    await fn()

    delay1 = times[1] - times[0]
    delay2 = times[2] - times[1]

    assert 0.04 < delay1 < 0.15
    assert 0.08 < delay2 < 0.25


@pytest.mark.asyncio
async def test_retry_sync_and_async():
    """Decorator works with both sync and async functions."""

    @retry(attempts=2, base_delay=0.01)
    def sync_fn():
        return "sync"

    @retry(attempts=2, base_delay=0.01)
    async def async_fn():
        return "async"

    assert await sync_fn() == "sync"  # type: ignore[misc]
    assert await async_fn() == "async"


def test_circuit_breaker_init():
    """Initializes closed with 0 failures."""
    cb = CircuitBreaker(max_failures=3)
    assert not cb.is_open()
    assert cb.consecutive_failures == 0


def test_circuit_breaker_opens_at_threshold():
    """Opens after max_failures consecutive failures."""
    cb = CircuitBreaker(max_failures=3)

    assert not cb.record_failure()
    assert not cb.record_failure()
    assert cb.record_failure()
    assert cb.is_open()


def test_circuit_breaker_resets_on_success():
    """Success resets failure counter."""
    cb = CircuitBreaker(max_failures=3)

    cb.record_failure()
    cb.record_failure()
    cb.record_success()

    assert cb.consecutive_failures == 0
    assert not cb.is_open()
