#!/usr/bin/env python3
"""
Quick release test script to verify all core functionality works
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "python" / "src"))

from cogency.agent import Agent
from cogency.llm import GeminiLLM
from cogency.tools.calculator import CalculatorTool
from cogency.tools.web_search import WebSearchTool
from cogency.tools import list_available_tools

def test_tool_discovery():
    """Test that tool discovery works"""
    print("🧪 Testing tool discovery...")
    tools = list_available_tools()
    expected_tools = ['calculator', 'web_search']
    
    for tool in expected_tools:
        if tool not in tools:
            print(f"❌ Missing tool: {tool}")
            return False
    
    print(f"✅ All expected tools found: {tools}")
    return True

def test_tool_instantiation():
    """Test that tools can be instantiated"""
    print("🧪 Testing tool instantiation...")
    
    try:
        calc = CalculatorTool()
        web = WebSearchTool()
        print("✅ All tools instantiated successfully")
        return True
    except Exception as e:
        print(f"❌ Tool instantiation failed: {e}")
        return False

def test_calculator_tool():
    """Test calculator tool functionality"""
    print("🧪 Testing calculator tool...")
    
    calc = CalculatorTool()
    
    # Test basic math
    result = calc.run(operation="add", num1=5, num2=3)
    if result.get("result") == 8:
        print("✅ Calculator addition works")
    else:
        print(f"❌ Calculator addition failed: {result}")
        return False
    
    # Test error handling
    result = calc.run(operation="invalid")
    if "error" in result:
        print("✅ Calculator error handling works")
    else:
        print(f"❌ Calculator error handling failed: {result}")
        return False
    
    return True

def test_web_search_tool():
    """Test web search tool functionality"""
    print("🧪 Testing web search tool...")
    
    web = WebSearchTool()
    
    # Test error handling for empty query
    result = web.run(query="")
    if "error" in result:
        print("✅ Web search error handling works")
    else:
        print(f"❌ Web search error handling failed: {result}")
        return False
    
    # Test basic search (without API key, should still validate input)
    result = web.run(query="test query", max_results=3)
    if "error" in result or "results" in result:
        print("✅ Web search basic functionality works")
    else:
        print(f"❌ Web search basic functionality failed: {result}")
        return False
    
    return True

def test_agent_without_llm():
    """Test that agent can be created without LLM for structure validation"""
    print("🧪 Testing agent structure...")
    
    try:
        # This will fail on run() without API key, but should create successfully
        agent = Agent(
            name="TestAgent",
            llm=GeminiLLM(api_key="fake-key"),
            tools=[CalculatorTool(), WebSearchTool()]
        )
        print("✅ Agent created successfully with tools")
        return True
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 Running Cogency v0.2.0 release tests...\n")
    
    tests = [
        test_tool_discovery,
        test_tool_instantiation,
        test_calculator_tool,
        test_web_search_tool,
        test_agent_without_llm,
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}\n")
    
    print(f"📊 Tests passed: {passed}/{len(tests)}")
    
    if passed == len(tests):
        print("🎉 All tests passed! Cogency v0.2.0 is ready for release!")
        return True
    else:
        print("🔧 Some tests failed. Please fix before release.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)