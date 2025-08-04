"""Agent tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from cogency.tools.shell import Shell
from tests.fixtures.llm import MockLLM


@pytest.mark.asyncio
async def test_defaults():
    agent = Agent("test_agent", llm=MockLLM(), tools="all")
    executor = await agent._get_executor()

    assert executor.llm is not None
    assert executor.memory is None

    tool_names = [tool.name for tool in executor.tools]
    assert "shell" in tool_names


@pytest.mark.asyncio
async def test_no_memory():
    agent = Agent("test", llm=MockLLM(), tools="all")
    executor = await agent._get_executor()

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
async def test_tools(memory_enabled, expected_tools):
    if memory_enabled:
        agent = Agent("test", llm=MockLLM(), tools=[Shell()], memory=True)
    else:
        agent = Agent("test", llm=MockLLM(), tools=[Shell()])

    executor = await agent._get_executor()
    tool_names = [tool.name for tool in executor.tools]
    for tool in expected_tools:
        assert tool in tool_names
    assert len(tool_names) == len(expected_tools)


@pytest.mark.asyncio
async def test_config_setup():
    agent = Agent("test", llm=MockLLM(), robust=True, observe=True, persist=True)
    executor = await agent._get_executor()

    assert executor.config.robust is not None
    assert executor.config.observe is not None
    assert executor.config.persist is not None


@pytest.mark.asyncio
async def test_config_custom():
    from cogency.config import ObserveConfig, PersistConfig, RobustConfig

    agent = Agent(
        "test",
        llm=MockLLM(),
        robust=RobustConfig(attempts=5),
        observe=ObserveConfig(metrics=False),
        persist=PersistConfig(enabled=True),
    )
    executor = await agent._get_executor()

    assert executor.config.robust.attempts == 5
    assert executor.config.observe.metrics is False
    assert executor.config.persist.enabled is True


@pytest.mark.asyncio
async def test_mode_assignment():
    agent = Agent("test", llm=MockLLM(), mode="fast", max_iterations=5)
    executor = await agent._get_executor()

    assert executor.mode == "fast"
    assert executor.max_iterations == 5


@pytest.mark.asyncio
async def test_identity():
    agent = Agent("test", llm=MockLLM(), identity="helpful assistant")
    executor = await agent._get_executor()

    assert executor.identity == "helpful assistant"


@pytest.mark.asyncio
async def test_output_schema():
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}
    agent = Agent("test", llm=MockLLM(), output_schema=schema)
    executor = await agent._get_executor()

    assert executor.output_schema == schema


@pytest.mark.asyncio
async def test_run():
    """Test that Agent can be created and has basic functionality."""
    agent = Agent("test", llm=MockLLM(), tools=[])

    # Test basic properties
    assert agent.name == "test"
    assert agent._config.name == "test"
    # Event bus architecture emits setup events, so logs won't be empty
    logs = agent.logs()
    assert isinstance(logs, list)


@pytest.mark.asyncio
async def test_run_config():
    """Test Agent configuration options work correctly."""
    agent = Agent("test", memory=True, debug=True, tools=["shell"])

    # Test config is properly set
    assert agent._config.memory is True
    assert agent._config.debug is True
    assert agent._config.tools == ["shell"]


def test_logs_available():
    agent = Agent("test", llm=MockLLM(), tools=[])
    # Event bus architecture means logs are available immediately
    logs = agent.logs()
    assert isinstance(logs, list)
