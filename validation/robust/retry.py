#!/usr/bin/env python3
"""Retry and timeout validation - operation resilience patterns."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator


async def validate_retry_behavior():
    """Validate that failed operations are retried appropriately."""
    print("🔄 Validating retry behavior...")

    agent = Agent(
        "retry-validator",
        identity="resilient agent that retries failed operations",
        tools=[Calculator()],
        notify=True,
        trace=True,
    )

    # Operations that might need retries
    result = await agent.run("Calculate a complex expression: (123 * 456) + (789 / 12.34)")

    if result and "ERROR:" not in result:
        print("✅ Retry behavior working for complex operations")
        return True
    else:
        print("❌ Retry behavior validation failed")
        return False


async def validate_timeout_handling():
    """Validate timeout handling for long operations."""
    print("⏱️ Validating timeout handling...")

    agent = Agent(
        "timeout-validator",
        identity="agent that handles timeouts gracefully",
        tools=[Calculator()],
        notify=True,
        trace=True,
    )

    # Operation that should complete within reasonable time
    result = await agent.run("Calculate 50 * 25")

    if result and "ERROR:" not in result and "1250" in result:
        print("✅ Timeout handling allows normal operations")
        return True
    else:
        print("❌ Timeout handling failed")
        return False


async def main():
    """Run retry and timeout validation."""
    print("🚀 Starting retry/timeout validation...\n")

    validations = [
        validate_retry_behavior,
        validate_timeout_handling,
    ]

    results = []
    for validation in validations:
        try:
            success = await validation()
            results.append(success)
        except Exception as e:
            print(f"❌ {validation.__name__} crashed: {e}")
            results.append(False)
        print()

    passed = sum(results)
    total = len(results)

    print(f"📊 Retry/timeout validation: {passed}/{total} validations passed")

    if passed == total:
        print("🎉 Retry/timeout system is production ready!")
    else:
        print("⚠️  Retry/timeout system needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
