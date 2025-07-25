"""Test circuit breaker for runaway protection."""

import asyncio
import time

import pytest

from cogency.resilience.decorators import safe


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    """Test circuit breaker opens after max failures."""

    @safe.circuit(max_failures=2, time_window=60)
    async def failing_function():
        raise Exception("Always fails")

    # First failure
    with pytest.raises(Exception, match="Always fails"):
        await failing_function()

    # Second failure - should still raise
    with pytest.raises(Exception, match="Always fails"):
        await failing_function()

    # Third call - circuit should be open
    result = await failing_function()
    assert "Circuit breaker open" in result
    assert "too many failures" in result


@pytest.mark.asyncio
async def test_circuit_breaker_resets_after_time_window():
    """Test circuit breaker resets after time window expires."""

    @safe.circuit(max_failures=1, time_window=0.1)  # 100ms window
    async def failing_then_working():
        if not hasattr(failing_then_working, "call_count"):
            failing_then_working.call_count = 0
        failing_then_working.call_count += 1

        if failing_then_working.call_count <= 1:
            raise Exception("Initial failure")
        return "success"

    # First call fails and opens circuit
    with pytest.raises(Exception, match="Initial failure"):
        await failing_then_working()

    # Second call - circuit should be open
    result = await failing_then_working()
    assert "Circuit breaker open" in result

    # Wait for time window to expire
    await asyncio.sleep(0.11)

    # Third call - circuit should be closed and function works
    result = await failing_then_working()
    assert result == "success"


@pytest.mark.asyncio
async def test_circuit_breaker_per_function_isolation():
    """Test circuit breaker isolates failures per function."""

    @safe.circuit(max_failures=1, time_window=60)
    async def function_a():
        raise Exception("Function A fails")

    @safe.circuit(max_failures=1, time_window=60)
    async def function_b():
        return "Function B works"

    # Function A fails and opens its circuit
    with pytest.raises(Exception, match="Function A fails"):
        await function_a()

    # Function A circuit is now open
    result_a = await function_a()
    assert "Circuit breaker open" in result_a

    # Function B should still work
    result_b = await function_b()
    assert result_b == "Function B works"


@pytest.mark.asyncio
async def test_circuit_breaker_successful_calls_dont_trigger():
    """Test successful calls don't trigger circuit breaker."""

    @safe.circuit(max_failures=3, time_window=60)  # Allow 3 failures
    async def sometimes_failing():
        if not hasattr(sometimes_failing, "call_count"):
            sometimes_failing.call_count = 0
        sometimes_failing.call_count += 1

        # Fail on odd calls, succeed on even calls
        if sometimes_failing.call_count % 2 == 1:
            raise Exception("Odd call fails")
        return f"Success on call {sometimes_failing.call_count}"

    # Call 1 - fails (1 failure)
    with pytest.raises(Exception, match="Odd call fails"):
        await sometimes_failing()

    # Call 2 - succeeds (still 1 failure)
    result = await sometimes_failing()
    assert result == "Success on call 2"

    # Call 3 - fails (2 failures)
    with pytest.raises(Exception, match="Odd call fails"):
        await sometimes_failing()

    # Call 4 - should still work (still 2 failures < 3)
    result = await sometimes_failing()
    assert result == "Success on call 4"

    # Call 5 - fails (3 failures, hits limit)
    with pytest.raises(Exception, match="Odd call fails"):
        await sometimes_failing()

    # Call 6 - circuit should now be open
    result = await sometimes_failing()
    assert "Circuit breaker open" in result
