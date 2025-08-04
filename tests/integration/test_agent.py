"""Agent integration tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from tests.fixtures.llm import MockLLM


@pytest.mark.asyncio
async def test_agent_defaults():
    from unittest.mock import AsyncMock, Mock

    with patch("cogency.runtime.AgentExecutor.configure", new_callable=AsyncMock) as mock_configure:
        # Mock executor with required attributes
        mock_executor = Mock()
        mock_executor.llm = MockLLM()
        mock_executor.memory = None
        shell_tool = Mock()
        shell_tool.name = "shell"
        mock_executor.tools = [shell_tool]
        mock_configure.return_value = mock_executor

        agent = Agent(name="test_agent", tools="all")

        # Trigger executor creation
        executor = agent._executor or await agent._get_executor()

        assert executor.llm is not None
        assert executor.memory is None  # Memory disabled by default

        tool_names = [tool.name for tool in executor.tools]
        assert "shell" in tool_names


@pytest.mark.asyncio
async def test_memory_disabled():
    from unittest.mock import AsyncMock, Mock

    with patch("cogency.runtime.AgentExecutor.configure", new_callable=AsyncMock) as mock_configure:
        # Mock executor with required attributes
        mock_executor = Mock()
        mock_executor.memory = None
        shell_tool = Mock()
        shell_tool.name = "shell"
        mock_executor.tools = [shell_tool]
        mock_configure.return_value = mock_executor

        agent = Agent(name="test", tools="all")

        # Trigger executor creation
        executor = agent._executor or await agent._get_executor()

        assert executor.memory is None
        tool_names = [tool.name for tool in executor.tools]
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

    with patch("cogency.runtime.AgentExecutor.configure", new_callable=AsyncMock) as mock_configure:
        # Mock executor with required attributes
        mock_executor = Mock()
        mock_executor.memory = Mock() if memory_enabled else None
        shell_tool = Mock()
        shell_tool.name = "shell"
        mock_executor.tools = [shell_tool]
        mock_configure.return_value = mock_executor

        if memory_enabled:
            agent = Agent("test", tools=[Shell()], memory=True)
        else:
            agent = Agent("test", tools=[Shell()])

        # Get executor to access tools
        executor = await agent._get_executor()

        tool_names = [tool.name for tool in executor.tools]
        for tool in expected_tools:
            assert tool in tool_names
        assert len(tool_names) == len(expected_tools)


@pytest.mark.asyncio
async def test_run():
    from unittest.mock import AsyncMock, Mock

    with patch("cogency.runtime.AgentExecutor.configure", new_callable=AsyncMock) as mock_configure:
        # Mock executor with run method
        mock_executor = Mock()
        mock_executor.run = AsyncMock(return_value="Final Answer")
        mock_configure.return_value = mock_executor

        agent = Agent(name="test", tools="all")
        result = await agent.run_async("test query")

        assert result == "Final Answer"
        mock_executor.run.assert_called_once_with("test query", "default", None)
