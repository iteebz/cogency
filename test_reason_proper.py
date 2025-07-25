#!/usr/bin/env python3
"""Test reason function with proper fixtures like conftest."""

import asyncio
from unittest.mock import AsyncMock, Mock
from typing import Dict, Any
from cogency.context import Context
from cogency.nodes.reason import reason
from cogency.output import Output
from .conftest import MockLLM
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.utils.results import ToolResult


class MockTool(BaseTool):
    def __init__(self):
        super().__init__(
            name="mock_tool",
            description="Mock tool for testing",
            emoji="🔧",
            schema="mock_tool(param='value')",
            examples=["mock_tool(param='test')"],
        )

    async def run(self, **kwargs):
        return ToolResult("mock_result")

    def format_human(self, params, results=None):
        param_str = f"({', '.join(f'{k}={v}' for k, v in params.items())})" if params else "()"
        result_str = str(results) if results else "pending"
        return param_str, result_str

    def format_agent(self, result_data: Dict[str, Any]) -> str:
        return f"Tool output: {result_data}"


async def test_reason():
    # Setup exactly like the test but with proper tools
    mock_context = Mock()
    mock_context.messages = []
    mock_context.query = "test query"

    state = State(context=mock_context, query="test query", output=Output())

    # Use proper MockLLM that returns Result objects
    mock_llm = MockLLM(response='{"reasoning": "test reasoning", "strategy": "test_strategy"}')

    # Use proper MockTool instead of broken Mock
    mock_tools = [MockTool()]

    print("Testing reason function with proper tools...")
    print("State type:", type(state))
    print("Has cognition?", hasattr(state, "cognition"))

    try:
        result = await reason(state, llm=mock_llm, tools=mock_tools)
        print("✅ Success! Result type:", type(result))
        print("✅ Has cognition?", hasattr(result, "cognition"))
        if hasattr(result, "cognition"):
            print("✅ Result is a proper State object")
            print("✅ Test would pass!")
            return True
        else:
            print("❌ Result is not a State object")
            return False
    except Exception as e:
        print("❌ Exception type:", type(e))
        print("❌ Exception message:", str(e))
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_reason())
    if success:
        print("\n🎉 The issue is in the test fixtures, not the resilient-result integration!")
        print("💡 Fix: Update tests to use proper BaseTool subclasses instead of Mock objects")
    else:
        print("\n😞 There are still issues to debug...")
