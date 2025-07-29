"""Agent integration tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from cogency.tools.calculator import Calculator
from tests.conftest import MockLLM


def test_agent_defaults():
    agent = Agent("test_agent", llm=MockLLM())

    assert agent.llm is not None
    assert agent.memory is not None

    tool_names = [tool.name for tool in agent.tools]
    assert "recall" in tool_names
    assert "calculator" in tool_names


def test_memory_disabled():
    agent = Agent("test", llm=MockLLM(), memory=False)

    assert agent.memory is None
    tool_names = [tool.name for tool in agent.tools]
    assert "recall" not in tool_names


@pytest.mark.parametrize(
    "memory_enabled,expected_tools",
    [
        (False, ["calculator"]),
        (True, ["calculator", "recall"]),
    ],
)
def test_custom_tools(memory_enabled, expected_tools):
    agent = Agent("test", llm=MockLLM(), tools=[Calculator()], memory=memory_enabled)

    tool_names = [tool.name for tool in agent.tools]
    for tool in expected_tools:
        assert tool in tool_names
    assert len(tool_names) == len(expected_tools)


@pytest.mark.asyncio
async def test_run():
    agent = Agent("test", llm=MockLLM())

    with patch("cogency.execution.run_agent", new_callable=AsyncMock) as mock_run_agent:
        mock_run_agent.return_value = "Final Answer"

        result = await agent.run("test query")

        mock_run_agent.assert_called_once()
        assert result is not None


@pytest.mark.asyncio
async def test_stream_validation():
    agent = Agent("test", llm=MockLLM())

    with patch("cogency.execution.run_agent", new_callable=AsyncMock) as mock_run_agent:
        # Empty query
        chunks = [chunk async for chunk in agent.stream("")]
        assert "Empty query not allowed" in chunks[0]
        mock_run_agent.assert_not_called()

        # Too long query
        long_query = "a" * 10001
        chunks = [chunk async for chunk in agent.stream(long_query)]
        assert "Query too long" in chunks[0]
        mock_run_agent.assert_not_called()
