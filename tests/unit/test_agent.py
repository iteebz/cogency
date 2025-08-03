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
    agent = Agent("test", llm=MockLLM(), tools=[])

    with patch(
        "cogency.steps.execution.execute_agent", new_callable=AsyncMock
    ) as mock_execute_agent:
        result = await agent.run_async("test query")
        mock_execute_agent.assert_called_once()
        assert result is not None


@pytest.mark.asyncio
async def test_run_error():
    agent = Agent("test", llm=MockLLM(), tools=[])

    with patch("cogency.security.assess", new_callable=AsyncMock) as mock_assess:
        # Mock security assessment to return safe
        from cogency.security import SecurityAction, SecurityResult

        mock_assess.return_value = SecurityResult(SecurityAction.ALLOW)

        with patch("cogency.steps.execution.execute_agent", side_effect=Exception("Test error")):
            with pytest.raises(Exception) as exc_info:
                await agent.run_async("test query")
            assert "Test error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_stream():
    agent = Agent("test", llm=MockLLM(), tools=[])

    with patch(
        "cogency.steps.execution.execute_agent", new_callable=AsyncMock
    ) as mock_execute_agent:
        # Empty query
        chunks = [chunk async for chunk in agent.stream("")]
        assert "Empty query not allowed" in chunks[0]
        mock_execute_agent.assert_not_called()

        # Too long query
        long_query = "a" * 10001
        chunks = [chunk async for chunk in agent.stream(long_query)]
        assert "Query too long" in chunks[0]
        mock_execute_agent.assert_not_called()


def test_logs_empty():
    agent = Agent("test", llm=MockLLM(), tools=[])
    assert agent.logs() == []


@pytest.mark.asyncio
async def test_setup_notifier():
    agent = Agent("test", llm=MockLLM(), tools=[])
    executor = await agent._get_executor()

    notifier = executor._setup_notifier()
    assert notifier is not None
    assert callable(notifier)
    assert hasattr(notifier, "emit")
    assert hasattr(notifier, "notifications")
