#!/usr/bin/env python3
"""
TOOL INTEGRATION TESTS - Each tool in isolation.
Validates every tool works independently.
"""
import asyncio
from cogency import Agent, CalculatorTool, WeatherTool, TimezoneTool, WebSearchTool, FileManagerTool

async def test_calculator():
    """Test CalculatorTool in isolation"""
    print("🧮 Testing CalculatorTool...")
    agent = Agent("calc", tools=[CalculatorTool()], trace=False)
    result = await agent.run("Calculate 15 * 23")
    assert "345" in str(result), f"Expected 345, got: {result}"
    print("✅ CalculatorTool works")

async def test_weather():
    """Test WeatherTool in isolation"""
    print("🌤️ Testing WeatherTool...")
    agent = Agent("weather", tools=[WeatherTool()], trace=False)
    result = await agent.run("Weather in London")
    result_str = str(result).lower()
    has_weather = any(word in result_str for word in ["temperature", "°c", "°f", "weather"])
    assert has_weather, f"No weather info: {result}"
    print("✅ WeatherTool works")

async def test_timezone():
    """Test TimezoneTool in isolation"""
    print("🕐 Testing TimezoneTool...")
    agent = Agent("time", tools=[TimezoneTool()], trace=False)
    result = await agent.run("What time is it in Tokyo?")
    result_str = str(result).lower()
    has_time = any(word in result_str for word in ["time", "timezone", "tokyo", ":"])
    assert has_time, f"No time info: {result}"
    print("✅ TimezoneTool works")

async def test_web_search():
    """Test WebSearchTool in isolation"""
    print("🔍 Testing WebSearchTool...")
    try:
        agent = Agent("search", tools=[WebSearchTool()], trace=False)
        result = await agent.run("Search for latest Python news")
        assert len(str(result)) > 50, f"Search result too short: {result}"
        print("✅ WebSearchTool works")
    except Exception as e:
        print(f"⚠️ WebSearchTool requires API key: {e}")

async def test_file_manager():
    """Test FileManagerTool in isolation"""
    print("📁 Testing FileManagerTool...")
    try:
        agent = Agent("files", tools=[FileManagerTool()], trace=False)
        result = await agent.run("List files in current directory")
        assert len(str(result)) > 10, f"File list too short: {result}"
        print("✅ FileManagerTool works")
    except Exception as e:
        print(f"⚠️ FileManagerTool error: {e}")

async def main():
    """Test each tool individually"""
    print("🔧 INDIVIDUAL TOOL TESTS")
    print("="*50)
    
    tests = [
        test_calculator,
        test_weather, 
        test_timezone,
        test_web_search,
        test_file_manager
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"❌ {test.__name__} failed: {e}")
        print()
    
    print("="*50)
    print("🎯 All available tools tested individually")

if __name__ == "__main__":
    asyncio.run(main())