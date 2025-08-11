"""Agent integration tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from cogency.tools import Shell
from tests.fixtures.provider import MockLLM


@pytest.mark.asyncio
async def test_agent_defaults():
    from unittest.mock import AsyncMock, Mock

    with patch("cogency.runtime.AgentRuntime.configure", new_callable=AsyncMock) as mock_configure:
        # Mock runtime with executor
        mock_runtime = Mock()
        mock_executor = Mock()
        mock_executor.llm = MockLLM()
        mock_executor.memory = None
        shell_tool = Mock()
        shell_tool.name = "shell"
        mock_executor.tools = [shell_tool]
        mock_runtime.executor = mock_executor
        mock_configure.return_value = mock_runtime

        agent = Agent(name="test_agent", tools=[Shell()])

        # Trigger executor creation
        runtime = agent._executor or await agent._get_executor()

        assert runtime.executor.llm is not None
        assert runtime.executor.memory is None  # Memory disabled by default

        tool_names = [tool.name for tool in runtime.executor.tools]
        assert "shell" in tool_names


@pytest.mark.asyncio
async def test_memory_disabled():
    from unittest.mock import AsyncMock, Mock

    with patch("cogency.runtime.AgentRuntime.configure", new_callable=AsyncMock) as mock_configure:
        # Mock runtime with executor
        mock_runtime = Mock()
        mock_executor = Mock()
        mock_executor.memory = None
        shell_tool = Mock()
        shell_tool.name = "shell"
        mock_executor.tools = [shell_tool]
        mock_runtime.executor = mock_executor
        mock_configure.return_value = mock_runtime

        agent = Agent(name="test", tools=[Shell()])

        # Trigger executor creation
        runtime = agent._executor or await agent._get_executor()

        assert runtime.executor.memory is None
        tool_names = [tool.name for tool in runtime.executor.tools]
        assert "shell" in tool_names


@pytest.mark.parametrize(
    "memory_enabled,expected_tools",
    [
        (False, ["shell"]),
        (True, ["shell"]),
    ],
    ids=["no_memory", "with_memory"],
)
@pytest.mark.asyncio
async def test_custom_tools(memory_enabled, expected_tools):
    from unittest.mock import AsyncMock, Mock

    from cogency.tools.shell import Shell

    with patch("cogency.runtime.AgentRuntime.configure", new_callable=AsyncMock) as mock_configure:
        # Mock runtime with executor
        mock_runtime = Mock()
        mock_executor = Mock()
        mock_executor.memory = Mock() if memory_enabled else None
        shell_tool = Mock()
        shell_tool.name = "shell"
        mock_executor.tools = [shell_tool]
        mock_runtime.executor = mock_executor
        mock_configure.return_value = mock_runtime

        if memory_enabled:
            agent = Agent("test", tools=[Shell()], memory=True)
        else:
            agent = Agent("test", tools=[Shell()])

        # Get runtime to access tools
        runtime = await agent._get_executor()

        tool_names = [tool.name for tool in runtime.executor.tools]
        for tool in expected_tools:
            assert tool in tool_names
        assert len(tool_names) == len(expected_tools)


@pytest.mark.asyncio
async def test_run():
    from unittest.mock import AsyncMock, Mock

    with patch("cogency.runtime.AgentRuntime.configure", new_callable=AsyncMock) as mock_configure:
        # Mock runtime with run method
        mock_runtime = Mock()
        mock_runtime.run = AsyncMock(return_value="Final Answer")
        mock_configure.return_value = mock_runtime

        agent = Agent(name="test", tools=[Shell()])
        result = await agent.run_async("test query")

        assert result == "Final Answer"
        mock_runtime.run.assert_called_once_with("test query", "default", None)
