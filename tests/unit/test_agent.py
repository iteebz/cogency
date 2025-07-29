"""Agent tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from cogency.config import Observe, Persist, Robust
from cogency.tools.calculator import Calculator
from tests.conftest import MockLLM


def test_defaults():
    agent = Agent(name="test_agent", llm=MockLLM())

    assert agent.llm is not None
    assert agent.memory is not None

    tool_names = [tool.name for tool in agent.tools]
    assert "recall" in tool_names
    assert "calculator" in tool_names


def test_no_memory():
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
    ids=["no_memory", "with_memory"],
)
def test_tools(memory_enabled, expected_tools):
    agent = Agent("test", llm=MockLLM(), tools=[Calculator()], memory=memory_enabled)

    tool_names = [tool.name for tool in agent.tools]
    for tool in expected_tools:
        assert tool in tool_names
    assert len(tool_names) == len(expected_tools)


def test_config_setup():
    agent = Agent("test", llm=MockLLM(), robust=True, observe=True, persist=True)

    assert agent.config.robust is not None
    assert agent.config.observe is not None
    assert agent.config.persist is not None


def test_config_custom():
    robust_config = Robust(attempts=5)
    observe_config = Observe(metrics=False)
    persist_config = Persist(enabled=False)

    agent = Agent(
        "test", llm=MockLLM(), robust=robust_config, observe=observe_config, persist=persist_config
    )

    assert agent.config.robust.attempts == 5
    assert agent.config.observe.metrics is False
    assert agent.config.persist.enabled is False


def test_mode_assignment():
    agent = Agent("test", llm=MockLLM(), mode="fast", depth=5)

    assert agent.mode == "fast"
    assert agent.depth == 5


def test_identity():
    agent = Agent("test", llm=MockLLM(), identity="helpful assistant")

    assert agent.identity == "helpful assistant"


def test_output_schema():
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}
    agent = Agent("test", llm=MockLLM(), output_schema=schema)

    assert agent.output_schema == schema


@pytest.mark.asyncio
async def test_run():
    agent = Agent("test", llm=MockLLM())

    with patch("cogency.execution.run_agent", new_callable=AsyncMock) as mock_run_agent:
        mock_run_agent.return_value = "Final Answer"
        result = await agent.run("test query")

        mock_run_agent.assert_called_once()
        assert result is not None


@pytest.mark.asyncio
async def test_run_error():
    agent = Agent("test", llm=MockLLM())

    with patch("cogency.execution.run_agent", side_effect=Exception("Test error")):
        try:
            await agent.run("test query")
            raise AssertionError("Should have raised exception")
        except Exception as e:
            assert "Test error" in str(e)


@pytest.mark.asyncio
async def test_stream():
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


def test_traces_empty():
    agent = Agent("test", llm=MockLLM())
    assert agent.traces() == []


def test_setup_notifier():
    agent = Agent("test", llm=MockLLM())

    notifier = agent._setup_notifier()
    assert notifier is not None
    assert hasattr(notifier, "preprocess")
    assert hasattr(notifier, "reason")
