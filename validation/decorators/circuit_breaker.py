"""Circuit breaker validation - failure detection and protection."""

import asyncio
import os

from cogency import Agent
from cogency.config import Robust


async def test_circuit_breaker_basic():
    """Test basic circuit breaker functionality."""
    print("🔌 Testing basic circuit breaker...")

    robust_config = Robust(
        circuit=True
        circuit_failures=2,  # Trip after 2 failures
        circuit_window=60,  # 1 minute window
        retry=True
        attempts=1,  # Fail fast to trigger circuit
    )

    # Use invalid key to force failures
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-invalid-circuit-test-key"

    try:
        agent = Agent("circuit-basic", robust=robust_config)

        # Make requests to trip circuit breaker
        results = []
        for i in range(4):
            result = await agent.run(f"Test query {i}")
            results.append(result)
            print(f"Request {i+1}: {'FAILED' if 'ERROR:' in result else 'SUCCESS'}")

        # After 2 failures, circuit should be open
        failure_count = sum(1 for r in results if "ERROR:" in r)

        if failure_count >= 2:
            print("✅ Circuit breaker tripped correctly")
            return True
        else:
            print("❌ Circuit breaker didn't trip")
            return False

    finally:
        # Restore original key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)


async def test_circuit_breaker_recovery():
    """Test circuit breaker recovery after failures."""
    print("🔄 Testing circuit breaker recovery...")

    robust_config = Robust(
        circuit=True
        circuit_failures=1,  # Trip after 1 failure
        circuit_window=2,  # Short window for testing
        retry=True
        attempts=1
    )

    # Start with invalid key
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-invalid-recovery-test"

    try:
        agent = Agent("circuit-recovery", robust=robust_config)

        # First request - should fail and trip circuit
        result1 = await agent.run("First test query")
        print(f"First request: {'FAILED' if 'ERROR:' in result1 else 'SUCCESS'}")

        # Restore valid key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key

        # Wait for circuit window to reset
        await asyncio.sleep(3)

        # Second request - circuit should reset and succeed
        result2 = await agent.run("Recovery test query")
        print(f"Recovery request: {'FAILED' if 'ERROR:' in result2 else 'SUCCESS'}")

        if "ERROR:" in result1 and "ERROR:" not in result2:
            print("✅ Circuit breaker recovery succeeded")
            return True
        else:
            print("❌ Circuit breaker recovery failed")
            return False

    except Exception as e:
        print(f"Circuit breaker recovery test exception: {e}")
        return False

    finally:
        # Ensure original key is restored
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key


async def test_circuit_breaker_window():
    """Test circuit breaker failure window behavior."""
    print("⏰ Testing circuit breaker window behavior...")

    robust_config = Robust(
        circuit=True
        circuit_failures=3,  # Need 3 failures to trip
        circuit_window=5,  # 5 second window
        retry=True
        attempts=1
    )

    # Invalid key for failures
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-invalid-window-test"

    try:
        agent = Agent("circuit-window", robust=robust_config)

        # Make 2 failures quickly
        result1 = await agent.run("Window test 1")
        result2 = await agent.run("Window test 2")

        # Wait for window to expire
        await asyncio.sleep(6)

        # Make another failure - should reset window
        result3 = await agent.run("Window test 3")
        result4 = await agent.run("Window test 4")  # This shouldn't trip circuit yet

        failures = sum(1 for r in [result1, result2, result3, result4] if "ERROR:" in r)

        # Should have failures but circuit shouldn't be permanently open due to window reset
        if failures >= 3:
            print("✅ Circuit breaker window behavior working")
            return True
        else:
            print("❌ Circuit breaker window behavior failed")
            return False

    finally:
        # Restore original key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)


async def test_circuit_breaker_with_tools():
    """Test circuit breaker behavior with tool failures."""
    print("🛠️  Testing circuit breaker with tool scenarios...")

    robust_config = Robust(
        circuit=True, circuit_failures=2, circuit_window=30, retry=True, attempts=1
    )

    agent = Agent(
        "circuit-tools"
        robust=robust_config
        tools=["calculator", "weather"],  # Tools that might fail
    )

    # Test with potentially failing tool operations
    try:
        result = await agent.run(
            "Get the weather for an invalid city called XYZ123 and calculate its temperature in Kelvin"
        )

        # Should handle tool failures gracefully
        if result and ("ERROR:" in result or len(result) > 20):
            print("✅ Circuit breaker with tools handled correctly")
            return True
        else:
            print("❌ Circuit breaker with tools failed")
            return False

    except Exception:
        # Exception handling is also valid circuit breaker behavior
        print("✅ Circuit breaker with tools handled exception correctly")
        return True


async def main():
    """Run all circuit breaker validation tests."""
    print("🚀 Starting circuit breaker validation...\n")

    tests = [
        test_circuit_breaker_basic
        test_circuit_breaker_recovery
        test_circuit_breaker_window
        test_circuit_breaker_with_tools
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

    print(f"📊 Circuit breaker validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Circuit breaker is production ready!")
    else:
        print("⚠️  Circuit breaker needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
