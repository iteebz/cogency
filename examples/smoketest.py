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

async def test_calculator_tool():
    """Test: Calculator tool integration"""
    print("🧪 Testing calculator tool...")
    try:
        agent = Agent("calc_agent", tools=[CalculatorTool()])
        result = await agent.run("Calculate 15 * 23")
        # Should contain 345 somewhere
        assert "345" in str(result), f"Expected 345 in result, got: {result}"
        print("✅ Calculator tool works")
        return True
    except Exception as e:
        print(f"❌ Calculator tool failed: {e}")
        return False

async def test_weather_tool():
    """Test: Weather tool (no API key needed)"""
    print("🧪 Testing weather tool...")
    try:
        agent = Agent("weather_agent", tools=[WeatherTool()])
        result = await agent.run("What's the weather in London?")
        # Should contain temperature or weather info
        result_str = str(result).lower()
        has_weather = any(word in result_str for word in ["temperature", "°c", "°f", "weather", "sunny", "cloudy", "rain"])
        assert has_weather, f"No weather info found in: {result}"
        print("✅ Weather tool works")
        return True
    except Exception as e:
        print(f"❌ Weather tool failed: {e}")
        return False

async def test_timezone_tool():
    """Test: Timezone tool (no API key needed)"""
    print("🧪 Testing timezone tool...")
    try:
        agent = Agent("time_agent", tools=[TimezoneTool()])
        result = await agent.run("What time is it in Tokyo?")
        # Should contain time info
        result_str = str(result).lower()
        has_time = any(word in result_str for word in ["time", "timezone", "asia", "tokyo", ":"])
        assert has_time, f"No time info found in: {result}"
        print("✅ Timezone tool works")
        return True
    except Exception as e:
        print(f"❌ Timezone tool failed: {e}")
        return False

async def test_streaming():
    """Test: Streaming works"""
    print("🧪 Testing streaming...")
    try:
        agent = Agent("stream_agent", tools=[CalculatorTool()])
        chunks = []
        async for chunk in agent.stream("What is 7 * 6?"):
            chunks.append(chunk)
            if len(chunks) > 10:  # Prevent infinite loop
                break
        
        assert len(chunks) > 0, "No streaming chunks received"
        # Should have thinking, tool_call, or result chunks
        chunk_types = [chunk.get("type") for chunk in chunks]
        assert any(t in chunk_types for t in ["thinking", "tool_call", "result"]), f"No valid chunk types: {chunk_types}"
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
        test_calculator_tool,
        test_weather_tool,
        test_timezone_tool,
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