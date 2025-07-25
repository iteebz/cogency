#!/usr/bin/env python3
"""Test checkpoint decorator fix."""

import asyncio
from unittest.mock import Mock
from cogency.context import Context
from cogency.nodes.preprocess import preprocess
from cogency.output import Output
from .conftest import MockLLM
from cogency.state import State
from cogency.tools.base import BaseTool
from cogency.utils.results import ToolResult
from cogency.services.memory.filesystem import FileBackend
import tempfile


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
        return "(mock)", "mock_result"

    def format_agent(self, result_data):
        return f"Mock tool output: {result_data}"


async def test_checkpoint_decorator():
    """Test that checkpoint decorator returns State objects."""

    # Setup test state exactly like a real workflow
    ctx = Context("test query")
    state = State(context=ctx, query="test query", output=Output())

    llm = MockLLM(response="Test response")
    tools = [MockTool()]

    # Create temp memory backend
    with tempfile.TemporaryDirectory() as tmpdir:
        memory = FileBackend(memory_dir=tmpdir)

        print("Testing preprocess function (has @safe.checkpoint)...")
        print("State type before:", type(state))

        try:
            # This should work without the decorator
            result = await preprocess(
                state, llm=llm, tools=tools, memory=memory, system_prompt="Test prompt"
            )

            print("✅ Success! Result type:", type(result))
            print("✅ Is State object?", isinstance(result, State))
            print("✅ Has cognition?", hasattr(result, "cognition"))

            if isinstance(result, State):
                print("✅ Checkpoint decorator fix working - returns State object!")
                return True
            else:
                print("❌ Still returning wrong type:", type(result))
                return False

        except Exception as e:
            print("❌ Exception:", str(e))
            import traceback

            traceback.print_exc()
            return False


if __name__ == "__main__":
    success = asyncio.run(test_checkpoint_decorator())
    if success:
        print("\n🎉 Checkpoint decorator is FIXED!")
        print("💡 Ready to restore @safe.checkpoint decorators")
    else:
        print("\n😞 Checkpoint decorator still has issues")
