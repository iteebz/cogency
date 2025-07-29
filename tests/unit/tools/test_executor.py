"""Test tool execution."""

from unittest.mock import AsyncMock, Mock

import pytest
from resilient_result import Result

from cogency.tools.base import BaseTool
from cogency.tools.executor import run_tools


class MockTool(BaseTool):
    def __init__(self, name: str = "test_tool", should_fail: bool = False):
        super().__init__(
            name=name,
            description=f"Mock tool: {name}",
            examples=[f'{{"name": "{name}", "args": {{"test": "value"}}}}'],
            rules=[],
        )
        self.should_fail = should_fail

    async def run(self, **kwargs):
        if self.should_fail:
            raise Exception("Tool execution failed")
        return Result.ok(f"success from {self.name}")

    def format_human(self, params, results=None):
        return f"({self.name})", str(results) if results else ""

    def format_agent(self, result_data: dict[str, any]) -> str:
        return f"Tool output: {result_data}"


@pytest.mark.asyncio
async def test_basic_execution():
    search_tool = MockTool("search")
    search_tool.run = AsyncMock(return_value=Result.ok("search results"))

    weather_tool = MockTool("weather")
    weather_tool.run = AsyncMock(return_value=Result.ok("sunny"))

    tools = [search_tool, weather_tool]
    state = Mock()
    state.notify = AsyncMock()

    tool_calls = [("search", {"query": "cats"}), ("weather", {"city": "SF"})]

    result = await run_tools(tool_calls, tools, state)

    assert result.success
    assert result.data["successful_count"] == 2


@pytest.mark.asyncio
async def test_file_shell_exec():
    file_tool = MockTool("create_file")
    file_tool.run = AsyncMock(return_value=Result.ok("file created"))

    shell_tool = MockTool("run_shell")
    shell_tool.run = AsyncMock(return_value=Result.ok("command executed"))

    tools = [file_tool, shell_tool]
    context = Mock()
    context.add_result = Mock()
    context.add_message = Mock()
    context.notify = AsyncMock()

    tool_calls = [
        ("create_file", {"path": "test.py", "content": "print('hello')"}),
        ("run_shell", {"command": "python test.py"}),
    ]

    result = await run_tools(tool_calls, tools, context)

    assert result.success
    assert result.data["successful_count"] == 2
