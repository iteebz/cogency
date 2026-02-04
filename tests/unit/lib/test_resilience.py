"""Unit tests for cogency/lib/resilience.py."""

import pytest

from cogency.lib.resilience import retry, timeout


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
    """Waits longer between retries (monotonically increasing)."""
    import time

    times: list[float] = []

    @retry(attempts=3, base_delay=0.05)
    async def fn():
        times.append(time.time())
        if len(times) < 3:
            raise ValueError()
        return "ok"

    await fn()

    delay1 = times[1] - times[0]
    delay2 = times[2] - times[1]

    assert delay1 > 0, "First retry should have delay"
    assert delay2 > delay1, "Exponential backoff: second delay > first"


@pytest.mark.asyncio
async def test_retry_sync_and_async():
    """Decorator works with both sync and async functions."""

    @retry(attempts=2, base_delay=0.01)
    def sync_fn():
        return "sync"

    @retry(attempts=2, base_delay=0.01)
    async def async_fn():
        return "async"

    assert sync_fn() == "sync"
    assert await async_fn() == "async"


def test_sync_retry_succeeds_after_transients():
    """Sync: retries on exception, succeeds when succeeds."""
    calls = 0

    @retry(attempts=3, base_delay=0.01)
    def fn():
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ValueError("transient")
        return "ok"

    assert fn() == "ok"
    assert calls == 3


def test_sync_retry_raises_after_exhaustion():
    """Sync: raises original exception after all attempts fail."""
    calls = 0

    @retry(attempts=3, base_delay=0.01)
    def fn():
        nonlocal calls
        calls += 1
        raise ValueError("persistent")

    with pytest.raises(ValueError, match="persistent"):
        fn()
    assert calls == 3


def test_sync_retry_exponential_backoff():
    """Sync: waits longer between retries."""
    import time

    times: list[float] = []

    @retry(attempts=3, base_delay=0.05)
    def fn():
        times.append(time.time())
        if len(times) < 3:
            raise ValueError()
        return "ok"

    fn()

    delay1 = times[1] - times[0]
    delay2 = times[2] - times[1]

    assert delay1 > 0
    assert delay2 > delay1


@pytest.mark.asyncio
async def test_timeout_within_limit():
    """Returns result when function completes in time."""
    import asyncio

    @timeout(seconds=1.0)
    async def fn():
        await asyncio.sleep(0.01)
        return "done"

    assert await fn() == "done"


@pytest.mark.asyncio
async def test_timeout_exceeded():
    """Raises TimeoutError when function takes too long."""
    import asyncio

    @timeout(seconds=0.05)
    async def fn():
        await asyncio.sleep(1.0)
        return "never"

    with pytest.raises(asyncio.TimeoutError):
        await fn()
