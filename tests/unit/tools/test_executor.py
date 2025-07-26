"""Test tool execution."""

from unittest.mock import AsyncMock, Mock

import pytest

from cogency.tools.executor import run_tools
from cogency.utils.results import ToolResult


@pytest.mark.asyncio
async def test_basic_execution():
    search_tool = Mock()
    search_tool.name = "search"
    search_tool.execute = AsyncMock(return_value=ToolResult("search results"))

    weather_tool = Mock()
    weather_tool.name = "weather"
    weather_tool.execute = AsyncMock(return_value=ToolResult("sunny"))

    tools = [search_tool, weather_tool]
    context = Mock()
    context.add_result = Mock()
    context.add_message = Mock()

    tool_calls = [("search", {"query": "cats"}), ("weather", {"city": "SF"})]

    result = await run_tools(tool_calls, tools, context)

    assert result.success
    assert result.data["successful_count"] == 2


@pytest.mark.asyncio
async def test_file_shell_exec():
    file_tool = Mock()
    file_tool.name = "create_file"
    file_tool.execute = AsyncMock(return_value=ToolResult("file created"))

    shell_tool = Mock()
    shell_tool.name = "run_shell"
    shell_tool.execute = AsyncMock(return_value=ToolResult("command executed"))

    tools = [file_tool, shell_tool]
    context = Mock()
    context.add_result = Mock()
    context.add_message = Mock()

    tool_calls = [
        ("create_file", {"path": "test.py", "content": "print('hello')"}),
        ("run_shell", {"command": "python test.py"}),
    ]

    result = await run_tools(tool_calls, tools, context)

    assert result.success
    assert result.data["successful_count"] == 2
