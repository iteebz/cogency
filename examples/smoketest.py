#!/usr/bin/env python3
"""
PRAGMATIC TEST - Validate core functionality works as advertised.
Not unit tests, INTEGRATION tests. Real shit that users will do.
"""
import asyncio
from cogency import Agent, CalculatorTool, WeatherTool, TimezoneTool

async def test_basic_agent():
    """Test: 3-line agent works"""
    print("🧪 Testing basic agent...")
    try:
        agent = Agent("assistant")
        result = await agent.run("What is 5 + 3?")
        assert "8" in str(result), f"Expected 8 in result, got: {result}"
        print("✅ Basic agent works")
        return True
    except Exception as e:
        print(f"❌ Basic agent failed: {e}")
        return False


async def test_streaming():
    """Test: Streaming works (character-by-character)"""
    print("🧪 Testing streaming...")
    try:
        agent = Agent("stream_agent", tools=[CalculatorTool()], trace=False)  # No trace for cleaner stream test
        chars = []
        async for char in agent.stream("What is 7 * 6?"):
            chars.append(char)
            if len(chars) > 100:  # Prevent infinite collection
                break
        
        result = "".join(chars)
        assert len(result) > 0, "No streaming content received"
        assert "42" in result, f"Expected 42 in streaming result: {result}"
        print("✅ Streaming works")
        return True
    except Exception as e:
        print(f"❌ Streaming failed: {e}")
        return False

async def test_tool_subsetting():
    """Test: PLAN correctly filters tools"""
    print("🧪 Testing tool subsetting...")
    try:
        # Agent with multiple tools
        agent = Agent("multi_agent", tools=[CalculatorTool(), WeatherTool(), TimezoneTool()])
        
        # Math query should primarily use calculator
        result = await agent.run("Calculate 12 * 12")
        assert "144" in str(result), f"Expected 144 in math result: {result}"
        
        # Weather query should use weather tool
        result = await agent.run("Weather in Paris")
        result_str = str(result).lower()
        has_weather = any(word in result_str for word in ["temperature", "weather", "°"])
        assert has_weather, f"No weather info in weather query: {result}"
        
        print("✅ Tool subsetting works")
        return True
    except Exception as e:
        print(f"❌ Tool subsetting failed: {e}")
        return False

async def main():
    """Run all pragmatic tests"""
    print("🚀 COGENCY INTEGRATION TESTS")
    print("="*50)
    
    tests = [
        test_basic_agent,
        test_streaming,
        test_tool_subsetting
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
        print()
    
    passed = sum(results)
    total = len(results)
    
    print("="*50)
    if passed == total:
        print(f"🎉 ALL TESTS PASSED ({passed}/{total})")
        print("🚀 Cogency is working beautifully!")
    else:
        print(f"⚠️  {passed}/{total} tests passed")
        print("🔧 Some functionality needs attention")
    
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)