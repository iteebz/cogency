"""Agent integration tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from tests.conftest import MockLLM


@pytest.mark.asyncio
async def test_agent_defaults():
    agent = Agent(name="test_agent", tools="all")

    # Trigger executor creation
    executor = agent._executor or await agent._get_executor()

    assert executor.llm is not None
    assert executor.memory is None  # Memory disabled by default

    tool_names = [tool.name for tool in executor.tools]
    assert "shell" in tool_names


@pytest.mark.asyncio
async def test_memory_disabled():
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
    from cogency.tools.shell import Shell

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
    agent = Agent(name="test", tools="all")

    with patch("cogency.steps.execution.run_agent", new_callable=AsyncMock) as mock_run_agent:
        mock_run_agent.return_value = "Final Answer"

        result = await agent.run("test query")

        mock_run_agent.assert_called_once()
        assert result is not None


@pytest.mark.asyncio
async def test_stream_validation():
    agent = Agent(name="test", tools="all")

    with patch("cogency.steps.execution.run_agent", new_callable=AsyncMock) as mock_run_agent:
        # Empty query
        chunks = [chunk async for chunk in agent.stream("")]
        assert "Empty query not allowed" in chunks[0]
        mock_run_agent.assert_not_called()

        # Too long query
        long_query = "a" * 10001
        chunks = [chunk async for chunk in agent.stream(long_query)]
        assert "Query too long" in chunks[0]
        mock_run_agent.assert_not_called()
