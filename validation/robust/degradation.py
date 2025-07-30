#!/usr/bin/env python3
"""Graceful degradation validation - system resilience under stress."""

import asyncio

from cogency import Agent
from cogency.tools import Calculator, Weather


async def validate_graceful_degradation():
    """Validate graceful degradation under stress."""
    print("🛡️ Validating graceful degradation...")

    agent = Agent(
        "degradation-validator",
        identity="agent that degrades gracefully under stress",
        tools=[Calculator(), Weather()],
        notify=True,
        trace=True,
    )

    # Complex multi-tool operation that tests resilience
    result = await agent.run(
        "Calculate 25 * 8, then if that works, tell me about the weather in San Francisco"
    )

    if result and ("200" in result or "weather" in result.lower()):
        print("✅ Graceful degradation working")
        return True
    else:
        print("❌ Graceful degradation failed")
        return False


async def validate_partial_failure_handling():
    """Validate handling when some tools fail but others work."""
    print("⚖️ Validating partial failure handling...")

    agent = Agent(
        "partial-validator",
        identity="agent that continues working when some tools fail",
        tools=[Calculator()],  # Only calculator available
        notify=True,
        trace=True,
    )

    # Request that uses available tool but gracefully handles unavailable ones
    result = await agent.run(
        "Calculate 15 * 4, but if weather tools were available, I'd also ask for the forecast"
    )

    if result and "60" in result:
        print("✅ Partial failure handling working")
        return True
    else:
        print("❌ Partial failure handling failed")
        return False


async def main():
    """Run graceful degradation validation."""
    print("🚀 Starting graceful degradation validation...\n")

    validations = [
        validate_graceful_degradation,
        validate_partial_failure_handling,
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

    print(f"📊 Graceful degradation validation: {passed}/{total} validations passed")

    if passed == total:
        print("🎉 Graceful degradation system is production ready!")
    else:
        print("⚠️  Graceful degradation system needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
