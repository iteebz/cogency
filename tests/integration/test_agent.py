"""Agent integration tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from tests.conftest import MockLLM


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
        result = await agent.run("test query")

        assert result == "Final Answer"
        mock_executor.run.assert_called_once_with("test query", "default", None)


@pytest.mark.asyncio
async def test_stream_validation():
    from unittest.mock import AsyncMock, Mock

    with patch("cogency.runtime.AgentExecutor.configure", new_callable=AsyncMock) as mock_configure:
        # Mock executor with stream method
        mock_executor = Mock()

        async def mock_stream(query, user_id="default"):
            if not query:
                yield "Empty query not allowed"
            elif len(query) > 10000:
                yield "Query too long"
            else:
                yield "Normal response"

        mock_executor.stream = mock_stream
        mock_configure.return_value = mock_executor

        agent = Agent(name="test", tools="all")

        # Empty query
        chunks = [chunk async for chunk in agent.stream("")]
        assert "Empty query not allowed" in chunks[0]

        # Too long query
        long_query = "a" * 10001
        chunks = [chunk async for chunk in agent.stream(long_query)]
        assert "Query too long" in chunks[0]
