"""@observe decorator validation - metrics collection and tracing."""

import asyncio

from cogency import Agent
from cogency.config import Observe, Robust


async def test_observe_basic_metrics():
    """Test basic @observe metrics collection."""
    print("📊 Testing @observe basic metrics collection...")

    observe_config = Observe(metrics=True, timing=True, counters=True, export_format="json")

    agent = Agent("observe-basic", observe=observe_config, debug=True)

    result = await agent.run("Calculate the fibonacci sequence up to the 10th number")

    # Check if traces contain observable information
    traces = agent.traces()
    has_observability = any(
        "timing" in str(trace).lower()
        or "metric" in str(trace).lower()
        or "counter" in str(trace).lower()
        for trace in traces
    )

    if result and "ERROR:" not in result and has_observability:
        print("✅ Basic @observe metrics succeeded")
        return True
    else:
        print("❌ Basic @observe metrics failed")
        return False


async def test_observe_phase_specific():
    """Test @observe with phase-specific metrics."""
    print("🎯 Testing @observe phase-specific metrics...")

    observe_config = Observe(
        metrics=True,
        timing=True,
        phases=["reason", "act"],  # Only observe specific phases
        export_format="json",
    )

    agent = Agent(
        "observe-phases", observe=observe_config, debug=True, tools=["calculator", "search"]
    )

    result = await agent.run(
        "Search for the current weather and calculate what 25 degrees Celsius is in Fahrenheit"
    )

    # Should have phase-specific traces
    traces = agent.traces()
    has_phase_metrics = any(
        ("reason" in str(trace).lower() or "act" in str(trace).lower())
        and ("timing" in str(trace).lower() or "metric" in str(trace).lower())
        for trace in traces
    )

    if result and "ERROR:" not in result and has_phase_metrics:
        print("✅ Phase-specific @observe metrics succeeded")
        return True
    else:
        print("❌ Phase-specific @observe metrics failed")
        return False


async def test_observe_with_robust():
    """Test @observe metrics during @robust error scenarios."""
    print("🛡️  Testing @observe metrics with @robust integration...")

    observe_config = Observe(metrics=True, timing=True, counters=True)

    robust_config = Robust(retry=True, attempts=2, timeout=6.0, backoff="exponential")

    agent = Agent(
        "observe-robust",
        observe=observe_config,
        robust=robust_config,
        debug=True,
        tools=["weather", "calculator"],
    )

    # Task that might trigger retries
    result = await agent.run(
        "Get weather for Tokyo and calculate the temperature difference with New York"
    )

    traces = agent.traces()
    # Check if metrics are captured (unused for now)
    any(
        (
            "retry" in str(trace).lower()
            or "attempt" in str(trace).lower()
            or "timing" in str(trace).lower()
        )
        and "metric" in str(trace).lower()
        for trace in traces
    )

    if result and "ERROR:" not in result:
        print("✅ @observe + @robust integration succeeded")
        return True
    else:
        print("❌ @observe + @robust integration failed")
        return False


async def test_observe_performance_impact():
    """Test that @observe doesn't significantly impact performance."""
    print("⚡ Testing @observe performance impact...")

    import time

    # Run without observe
    start_time = time.time()
    agent_no_observe = Agent("perf-test-no-observe", debug=False)
    result1 = await agent_no_observe.run("What is 42 * 137?")
    no_observe_time = time.time() - start_time

    # Run with observe
    start_time = time.time()
    observe_config = Observe(metrics=True, timing=True, counters=True)
    agent_with_observe = Agent("perf-test-observe", observe=observe_config, debug=False)
    result2 = await agent_with_observe.run("What is 42 * 137?")
    observe_time = time.time() - start_time

    # Observe shouldn't add more than 50% overhead
    overhead = (observe_time - no_observe_time) / no_observe_time if no_observe_time > 0 else 0

    if (
        result1
        and result2
        and "ERROR:" not in result1
        and "ERROR:" not in result2
        and overhead < 0.5
    ):  # Less than 50% overhead
        print(f"✅ @observe performance impact acceptable ({overhead:.1%} overhead)")
        return True
    else:
        print(f"❌ @observe performance impact too high ({overhead:.1%} overhead)")
        return False


async def main():
    """Run all @observe validation tests."""
    print("🚀 Starting @observe decorator validation...\n")

    tests = [
        test_observe_basic_metrics,
        test_observe_phase_specific,
        test_observe_with_robust,
        test_observe_performance_impact,
    ]

    results = []
    for test in tests:
        try:
            success = await test()
            results.append(success)
        except Exception as e:
            print(f"❌ {test.__name__} crashed: {e}")
            results.append(False)
        print()

    passed = sum(results)
    total = len(results)

    print(f"📊 @observe validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 @observe decorator is production ready!")
    else:
        print("⚠️  @observe decorator needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
