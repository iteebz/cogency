"""Agent integration tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from cogency.tools.calculator import Calculator
from tests.conftest import MockLLM


def test_agent_defaults():
    """Agent has sane defaults with memory and recall."""
    agent = Agent("test_agent", llm=MockLLM())

    assert agent.flow is not None
    assert agent.flow.memory is not None

    tool_names = [tool.name for tool in agent.flow.tools]
    assert "recall" in tool_names
    assert "calculator" in tool_names


def test_agent_memory_disabled():
    """Agent without memory excludes recall tool."""
    agent = Agent("test", llm=MockLLM(), memory=False)

    assert agent.flow.memory is None
    tool_names = [tool.name for tool in agent.flow.tools]
    assert "recall" not in tool_names


@pytest.mark.parametrize(
    "memory_enabled,expected_tools",
    [
        (False, ["calculator"]),
        (True, ["calculator", "recall"]),
    ],
)
def test_custom_tools_with_memory(memory_enabled, expected_tools):
    """Custom tools work correctly with/without memory."""
    agent = Agent("test", llm=MockLLM(), tools=[Calculator()], memory=memory_enabled)

    tool_names = [tool.name for tool in agent.flow.tools]
    for tool in expected_tools:
        assert tool in tool_names
    assert len(tool_names) == len(expected_tools)


@pytest.mark.asyncio
async def test_run_invokes_flow():
    """Agent.run properly invokes flow execution."""
    agent = Agent("test", llm=MockLLM())

    with patch.object(agent.flow.flow, "ainvoke", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "Final Answer"

        result = await agent.run("test query")

        mock_execute.assert_called_once()
        assert result is not None


@pytest.mark.asyncio
async def test_stream_validation():
    """Stream handles invalid queries correctly."""
    agent = Agent("test", llm=MockLLM())

    with patch.object(agent.flow.flow, "ainvoke", new_callable=AsyncMock) as mock_execute:
        # Empty query
        chunks = [chunk async for chunk in agent.stream("")]
        assert "Empty query not allowed" in chunks[0]
        mock_execute.assert_not_called()

        # Too long query
        long_query = "a" * 10001
        chunks = [chunk async for chunk in agent.stream(long_query)]
        assert "Query too long" in chunks[0]
        mock_execute.assert_not_called()
