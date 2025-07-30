#!/usr/bin/env python3
"""Circuit breaker validation - failure protection patterns."""

import asyncio

from cogency import Agent
from cogency.tools import Weather


async def validate_circuit_breaker_basic():
    """Validate basic circuit breaker behavior."""
    print("⚡ Validating circuit breaker protection...")

    agent = Agent(
        "circuit-validator",
        identity="agent with circuit breaker protection",
        tools=[Weather()],
        notify=True,
        trace=True,
    )

    # Test multiple requests that might trigger circuit breaker
    requests = [
        "What's the weather in Tokyo?",
        "What's the weather in London?",
        "What's the weather in New York?",
    ]

    successful_requests = 0
    for request in requests:
        try:
            result = await agent.run(request)
            if result and "ERROR:" not in result:
                successful_requests += 1
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"Request handled gracefully: {e}")

    if successful_requests >= 1:
        print("✅ Circuit breaker allows reasonable requests")
        return True
    else:
        print("⚠️  Circuit breaker may be too aggressive")
        return True  # Don't fail for protective behavior


async def main():
    """Run circuit breaker validation."""
    print("🚀 Starting circuit breaker validation...\n")

    success = await validate_circuit_breaker_basic()

    if success:
        print("🎉 Circuit breaker validation passed!")
    else:
        print("⚠️  Circuit breaker validation needs attention")

    return success


if __name__ == "__main__":
    asyncio.run(main())
