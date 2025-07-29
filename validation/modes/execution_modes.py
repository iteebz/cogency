"""Agent execution modes validation - fast/deep/adapt behavior."""

import asyncio

from cogency import Agent


async def test_fast_mode():
    """Test fast mode execution - minimal depth, quick responses."""
    print("🏃 Testing fast mode execution...")

    agent = Agent("fast-mode-test", mode="fast", debug=True)

    result = await agent.run("What is 2+2 and explain it simply?")

    # Fast mode should provide quick, direct answers
    if (
        result and "ERROR:" not in result and "4" in result and len(result) < 200
    ):  # Should be concise
        print("✅ Fast mode execution succeeded")
        return True
    else:
        print("❌ Fast mode execution failed")
        return False


async def test_deep_mode():
    """Test deep mode execution - thorough analysis and reasoning."""
    print("🔬 Testing deep mode execution...")

    agent = Agent("deep-mode-test", mode="deep", depth=15, debug=True)

    result = await agent.run("Analyze the pros and cons of renewable energy")

    # Deep mode should provide comprehensive analysis
    if (
        result
        and "ERROR:" not in result
        and len(result) > 300
        and ("pros" in result.lower() or "advantages" in result.lower())  # Should be detailed
        and ("cons" in result.lower() or "disadvantages" in result.lower())
    ):
        print("✅ Deep mode execution succeeded")
        return True
    else:
        print("❌ Deep mode execution failed")
        return False


async def test_adapt_mode():
    """Test adaptive mode - adjusts based on query complexity."""
    print("🎯 Testing adaptive mode execution...")

    agent = Agent("adapt-mode-test", mode="adapt", debug=True)

    # Simple query - should be handled quickly
    result1 = await agent.run("What's the capital of France?")

    # Complex query - should trigger deeper reasoning
    result2 = await agent.run(
        "Compare the economic implications of different monetary policies during inflation"
    )

    if (
        result1
        and result2
        and "ERROR:" not in result1
        and "ERROR:" not in result2
        and "paris" in result1.lower()
        and len(result1) < len(result2)
    ):  # Complex query should be longer
        print("✅ Adaptive mode execution succeeded")
        return True
    else:
        print("❌ Adaptive mode execution failed")
        return False


async def test_depth_limits():
    """Test depth parameter enforcement."""
    print("📏 Testing depth limits...")

    # Very shallow depth
    agent_shallow = Agent("depth-shallow", depth=2, debug=True)

    # Normal depth
    agent_normal = Agent("depth-normal", depth=10, debug=True)

    query = "Explain quantum computing and its applications"

    result_shallow = await agent_shallow.run(query)
    result_normal = await agent_normal.run(query)

    if (
        result_shallow
        and result_normal
        and "ERROR:" not in result_shallow
        and "ERROR:" not in result_normal
        and len(result_shallow) <= len(result_normal)
    ):  # Shallow should be more limited
        print("✅ Depth limits working correctly")
        return True
    else:
        print("❌ Depth limits failed")
        return False


async def main():
    """Run all execution mode validation tests."""
    print("🚀 Starting execution modes validation...\n")

    tests = [test_fast_mode, test_deep_mode, test_adapt_mode, test_depth_limits]

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

    print(f"📊 Execution modes validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 Execution modes are production ready!")
    else:
        print("⚠️  Execution modes need attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
