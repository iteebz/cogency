"""Comprehensive tools validation - test all available tools."""

import asyncio
import tempfile
from pathlib import Path

from cogency import Agent


async def test_calculator_tool():
    """Test calculator tool functionality."""
    print("🧮 Testing calculator tool...")

    agent = Agent("tools-calculator", tools=["calculator"])

    result = await agent.run("Calculate 15 * 23 + 47")

    # Should get correct answer: 15 * 23 + 47 = 345 + 47 = 392
    if (
        result
        and "ERROR:" not in result
        and ("392" in result or "three hundred ninety" in result.lower())
    ):
        print("✅ Calculator tool succeeded")
        return True
    else:
        print("❌ Calculator tool failed")
        return False


async def test_files_tool():
    """Test files tool functionality."""
    print("📁 Testing files tool...")

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file = Path(temp_dir) / "test.txt"
        test_file.write_text("Hello from cogency validation!")

        agent = Agent("tools-files", tools=["files"])

        result = await agent.run(f"Read the contents of the file at {test_file}")

        if result and "ERROR:" not in result and "hello from cogency validation" in result.lower():
            print("✅ Files tool succeeded")
            return True
        else:
            print("❌ Files tool failed")
            return False


async def test_date_time_tools():
    """Test date and time tools."""
    print("⏰ Testing date and time tools...")

    agent = Agent("tools-datetime", tools=["date", "time"])

    result = await agent.run("What is today's date and current time?")

    # Should contain date/time information
    import datetime

    current_year = str(datetime.datetime.now().year)

    if result and "ERROR:" not in result and current_year in result:
        print("✅ Date/time tools succeeded")
        return True
    else:
        print("❌ Date/time tools failed")
        return False


async def test_search_tool():
    """Test search tool functionality."""
    print("🔍 Testing search tool...")

    agent = Agent("tools-search", tools=["search"])

    result = await agent.run("Search for information about Python programming language")

    if result and "ERROR:" not in result and "python" in result.lower() and len(result) > 100:
        print("✅ Search tool succeeded")
        return True
    else:
        print("❌ Search tool failed")
        return False


async def test_weather_tool():
    """Test weather tool functionality."""
    print("🌤️  Testing weather tool...")

    agent = Agent("tools-weather", tools=["weather"])

    result = await agent.run("What's the weather like in New York?")

    if (
        result
        and "ERROR:" not in result
        and ("weather" in result.lower() or "temperature" in result.lower())
    ):
        print("✅ Weather tool succeeded")
        return True
    else:
        print("❌ Weather tool failed")
        return False


async def test_code_tool():
    """Test code execution tool."""
    print("💻 Testing code tool...")

    agent = Agent("tools-code", tools=["code"])

    result = await agent.run("Execute this Python code: print('Hello from code tool!')")

    if result and "ERROR:" not in result and "hello from code tool" in result.lower():
        print("✅ Code tool succeeded")
        return True
    else:
        print("❌ Code tool failed")
        return False


async def test_http_tool():
    """Test HTTP requests tool."""
    print("🌐 Testing HTTP tool...")

    agent = Agent("tools-http", tools=["http"])

    result = await agent.run("Make a GET request to httpbin.org/json")

    if (
        result
        and "ERROR:" not in result
        and ("json" in result.lower() or "response" in result.lower())
    ):
        print("✅ HTTP tool succeeded")
        return True
    else:
        print("❌ HTTP tool failed")
        return False


async def test_multiple_tools_integration():
    """Test multiple tools working together."""
    print("🔧 Testing multiple tools integration...")

    agent = Agent("tools-integration", tools=["calculator", "date", "files"])

    with tempfile.TemporaryDirectory() as temp_dir:
        result = await agent.run(
            f"Calculate 100 + 50, get today's date, and create a file at {temp_dir}/result.txt with both pieces of information"
        )

        result_file = Path(temp_dir) / "result.txt"

        if result and "ERROR:" not in result and ("150" in result or result_file.exists()):
            print("✅ Multiple tools integration succeeded")
            return True
        else:
            print("❌ Multiple tools integration failed")
            return False


async def test_recall_tool():
    """Test recall (memory) tool functionality."""
    print("🧠 Testing recall tool...")

    agent = Agent("tools-recall", tools=["recall"])

    # First, store some information
    result1 = await agent.run("Remember that my favorite programming language is Rust")

    # Then try to recall it
    result2 = await agent.run("What programming language do I prefer?")

    if (
        result1
        and result2
        and "ERROR:" not in result1
        and "ERROR:" not in result2
        and "rust" in result2.lower()
    ):
        print("✅ Recall tool succeeded")
        return True
    else:
        print("❌ Recall tool failed")
        return False


async def main():
    """Run all tools validation tests."""
    print("🚀 Starting comprehensive tools validation...\n")

    tests = [
        test_calculator_tool
        test_files_tool
        test_date_time_tools
        test_search_tool
        test_weather_tool
        test_code_tool
        test_http_tool
        test_recall_tool
        test_multiple_tools_integration
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

    print(f"📊 Tools validation: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tools are production ready!")
    else:
        print("⚠️  Some tools need attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
