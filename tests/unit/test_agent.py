"""Agent tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from cogency.tools.shell import Shell
from tests.fixtures.llm import MockLLM


@pytest.mark.asyncio
async def test_defaults():
    agent = Agent("test_agent", llm=MockLLM(), tools="all")
    runtime = await agent._get_executor()

    assert runtime.executor.llm is not None
    assert runtime.executor.memory is None

    tool_names = [tool.name for tool in runtime.executor.tools]
    assert "shell" in tool_names


@pytest.mark.asyncio
async def test_no_memory():
    agent = Agent("test", llm=MockLLM(), tools="all")
    runtime = await agent._get_executor()

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
async def test_tools(memory_enabled, expected_tools):
    if memory_enabled:
        agent = Agent("test", llm=MockLLM(), tools=[Shell()], memory=True)
    else:
        agent = Agent("test", llm=MockLLM(), tools=[Shell()])

    runtime = await agent._get_executor()
    tool_names = [tool.name for tool in runtime.executor.tools]
    for tool in expected_tools:
        assert tool in tool_names
    assert len(tool_names) == len(expected_tools)


@pytest.mark.asyncio
async def test_config_setup():
    agent = Agent("test", llm=MockLLM(), robust=True, persist=True)
    runtime = await agent._get_executor()

    assert runtime.executor.config.robust is not None
    assert runtime.executor.config.persist is not None


@pytest.mark.asyncio
async def test_config_custom():
    from cogency.config import PersistConfig, RobustConfig

    agent = Agent(
        "test",
        llm=MockLLM(),
        robust=RobustConfig(attempts=5),
        persist=PersistConfig(enabled=True),
    )
    runtime = await agent._get_executor()

    assert runtime.executor.config.robust.attempts == 5
    assert runtime.executor.config.persist.enabled is True


@pytest.mark.asyncio
async def test_mode_assignment():
    agent = Agent("test", llm=MockLLM(), mode="fast", max_iterations=5)
    runtime = await agent._get_executor()

    # Mode is not directly on executor, but max_iterations is
    assert runtime.executor.max_iterations == 5


@pytest.mark.asyncio
async def test_identity():
    agent = Agent("test", llm=MockLLM(), identity="helpful assistant")
    runtime = await agent._get_executor()

    assert runtime.executor.identity == "helpful assistant"


@pytest.mark.asyncio
async def test_output_schema():
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}
    agent = Agent("test", llm=MockLLM(), output_schema=schema)
    runtime = await agent._get_executor()

    assert runtime.executor.output_schema == schema


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
    agent = Agent("test", memory=True, debug=True, tools=[Shell()])

    # Test config is properly set
    assert agent._config.memory is True
    assert agent._config.debug is True
    assert len(agent._config.tools) == 1
    assert agent._config.tools[0].name == "shell"


def test_logs_available():
    agent = Agent("test", llm=MockLLM(), tools=[])
    # Event bus architecture means logs are available immediately
    logs = agent.logs()
    assert isinstance(logs, list)


def test_logs_filtering_parameters():
    """Test Agent.logs() filtering functionality."""
    from unittest.mock import patch

    agent = Agent("test", llm=MockLLM(), tools=[])

    # Mock the get_logs function to verify parameters are passed correctly
    with patch("cogency.events.get_logs") as mock_get_logs:
        mock_get_logs.return_value = []

        # Test all filtering parameters
        agent.logs(type="tool", step="reason", raw=True, errors_only=True, last=5)

        mock_get_logs.assert_called_once_with(
            type="tool", step="reason", summary=False, errors_only=True, last=5
        )


def test_logs_filtering_examples():
    """Test Agent.logs() filtering examples from docstring."""
    from unittest.mock import patch

    agent = Agent("test", llm=MockLLM(), tools=[])

    with patch("cogency.events.get_logs") as mock_get_logs:
        mock_get_logs.return_value = []

        # Basic usage examples - now defaults to summary=True
        agent.logs()
        mock_get_logs.assert_called_with(
            type=None, step=None, summary=True, errors_only=False, last=None
        )

        agent.logs(errors_only=True)
        mock_get_logs.assert_called_with(
            type=None, step=None, summary=False, errors_only=True, last=None
        )

        agent.logs(last=10)
        mock_get_logs.assert_called_with(
            type=None, step=None, summary=True, errors_only=False, last=10
        )

        # Filtering examples - specific filters disable summary mode
        agent.logs(type="tool")
        mock_get_logs.assert_called_with(
            type="tool", step=None, summary=False, errors_only=False, last=None
        )

        agent.logs(step="reason")
        mock_get_logs.assert_called_with(
            type=None, step="reason", summary=False, errors_only=False, last=None
        )

        agent.logs(type="error", last=5)
        mock_get_logs.assert_called_with(
            type="error", step=None, summary=False, errors_only=False, last=5
        )

        # Raw mode examples
        agent.logs(raw=True)
        mock_get_logs.assert_called_with(
            type=None, step=None, summary=False, errors_only=False, last=None
        )
