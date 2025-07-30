"""@robust decorator validation - error handling and recovery with real LLMs."""

import asyncio
import os

from cogency import Agent
from cogency.config import Robust


async def test_robust_retry_backoff():
    """Test @robust with retry and exponential backoff."""
    print("🔥 Testing @robust retry with exponential backoff...")

    robust_config = Robust(
        retry=True
        attempts=3
        timeout=10.0
        backoff="exponential"
        backoff_delay=0.5
        backoff_factor=2.0
        backoff_max=5.0
    )

    agent = Agent("robust-retry", robust=robust_config)

    result = await agent.run("Generate a detailed analysis of renewable energy trends in 2024")

    print(f"Result: {result[:100]}...")
    if "ERROR:" not in result:
        print("✅ @robust retry succeeded")
        return True
    else:
        print("❌ @robust retry failed")
        return False


async def test_robust_timeout_handling():
    """Test @robust timeout handling."""
    print("⏱️  Testing @robust timeout handling...")

    robust_config = Robust(
        retry=True
        attempts=2
        timeout=3.0,  # Very short timeout
        backoff="fixed"
        backoff_delay=0.1
    )

    agent = Agent("robust-timeout", robust=robust_config)

    result = await agent.run("Write a comprehensive 5000-word essay on quantum computing")

    # Should either succeed quickly or timeout gracefully
    if result and ("ERROR:" in result or len(result) > 50):
        print("✅ @robust timeout handled correctly")
        return True
    else:
        print("❌ @robust timeout handling failed")
        return False


async def test_robust_invalid_key_recovery():
    """Test @robust recovery from invalid API key."""
    print("🔑 Testing @robust recovery from authentication errors...")

    # Temporarily set invalid key
    original_key = os.environ.get("OPENAI_API_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-invalid-key-test-12345"

    try:
        robust_config = Robust(
            retry=True, attempts=2, timeout=5.0, backoff="linear", backoff_delay=0.2
        )

        agent = Agent("robust-auth", robust=robust_config)

        result = await agent.run("Simple test query")

        # Should get proper error message, not crash
        if "ERROR:" in result or "authentication" in result.lower():
            print("✅ @robust authentication error handled correctly")
            success = True
        else:
            print("❌ @robust authentication error handling failed")
            success = False

    finally:
        # Restore original key
        if original_key:
            os.environ["OPENAI_API_KEY"] = original_key
        else:
            os.environ.pop("OPENAI_API_KEY", None)

    return success


async def main():
    """Run all @robust validation tests."""
    print("🚀 Starting @robust decorator validation...\n")

    tests = [
        test_robust_retry_backoff
        test_robust_timeout_handling
        test_robust_invalid_key_recovery
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

    print(f"📊 @robust validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 @robust decorator is production ready!")
    else:
        print("⚠️  @robust decorator needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
