"""@rate_limit validation - throttling and burst handling."""

import asyncio
import time

from cogency import Agent
from cogency.config import Robust


async def test_rate_limit_basic_throttling():
    """Test basic rate limiting throttling."""
    print("⚡ Testing basic rate limit throttling...")

    robust_config = Robust(
        rate_limit=True, rate_limit_rps=2.0, retry=True, attempts=2  # 2 requests per second
    )

    agent = Agent("rate-limit-basic", robust=robust_config, debug=True)

    # Fire 3 rapid requests
    start_time = time.time()
    tasks = [agent.run(f"What is {i} + {i}?") for i in range(3)]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    total_time = time.time() - start_time

    # Should take at least 1 second due to rate limiting (3 requests at 2 RPS)
    successful_results = [r for r in results if isinstance(r, str) and "ERROR:" not in r]

    if len(successful_results) >= 2 and total_time >= 0.8:  # Some tolerance
        print(f"✅ Rate limiting throttling worked ({total_time:.1f}s for 3 requests)")
        return True
    else:
        print(f"❌ Rate limiting failed ({len(successful_results)} successful, {total_time:.1f}s)")
        return False


async def test_rate_limit_burst_handling():
    """Test rate limit burst capacity."""
    print("💥 Testing rate limit burst handling...")

    robust_config = Robust(
        rate_limit=True,
        rate_limit_rps=1.0,  # 1 request per second
        rate_limit_burst=3,  # But allow 3 request burst
        retry=True,
        attempts=2,
    )

    agent = Agent("rate-limit-burst", robust=robust_config, debug=True)

    # Fire burst of requests within burst limit
    start_time = time.time()
    tasks = [agent.run(f"Calculate {i} * 2") for i in range(3)]  # Within burst limit

    results = await asyncio.gather(*tasks, return_exceptions=True)
    burst_time = time.time() - start_time

    successful_results = [r for r in results if isinstance(r, str) and "ERROR:" not in r]

    # Burst should complete quickly, then subsequent requests should be throttled
    if len(successful_results) >= 2 and burst_time < 2.0:  # Burst should be fast
        print(
            f"✅ Rate limit burst handling worked ({len(successful_results)} requests in {burst_time:.1f}s)"
        )
        return True
    else:
        print(
            f"❌ Rate limit burst failed ({len(successful_results)} successful, {burst_time:.1f}s)"
        )
        return False


async def test_rate_limit_with_retries():
    """Test rate limiting combined with retry logic."""
    print("🔄 Testing rate limit with retry integration...")

    robust_config = Robust(
        rate_limit=True,
        rate_limit_rps=1.5,
        retry=True,
        attempts=3,
        backoff="linear",
        backoff_delay=0.2,
        timeout=10.0,
    )

    agent = Agent("rate-limit-retry", robust=robust_config, debug=True)

    # Send requests that might hit rate limits and need retries
    tasks = [agent.run(f"Simple math: what is {i} squared?") for i in range(2)]

    results = await asyncio.gather(*tasks, return_exceptions=True)
    successful_results = [r for r in results if isinstance(r, str) and "ERROR:" not in r]

    if len(successful_results) >= 1:  # At least one should succeed despite rate limiting
        print("✅ Rate limiting with retries succeeded")
        return True
    else:
        print("❌ Rate limiting with retries failed")
        return False


async def test_rate_limit_aggressive_scenario():
    """Test rate limiting under aggressive load."""
    print("🔥 Testing aggressive rate limiting scenario...")

    robust_config = Robust(
        rate_limit=True,
        rate_limit_rps=0.5,  # Very aggressive - 1 request per 2 seconds
        retry=True,
        attempts=2,
        timeout=8.0,
    )

    agent = Agent("rate-limit-aggressive", robust=robust_config, debug=True)

    # Single request should work despite aggressive limiting
    start_time = time.time()
    result = await agent.run("What is the capital of France?")
    request_time = time.time() - start_time

    if result and "ERROR:" not in result:
        print(f"✅ Aggressive rate limiting handled correctly ({request_time:.1f}s)")
        return True
    else:
        print(f"❌ Aggressive rate limiting failed: {result}")
        return False


async def main():
    """Run all rate limiting validation tests."""
    print("🚀 Starting rate limiting validation...\n")

    tests = [
        test_rate_limit_basic_throttling,
        test_rate_limit_burst_handling,
        test_rate_limit_with_retries,
        test_rate_limit_aggressive_scenario,
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

    print(f"📊 Rate limiting validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Rate limiting is production ready!")
    else:
        print("⚠️  Rate limiting needs attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
