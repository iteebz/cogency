"""Agent tests - beautiful architecture edition."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent, AgentBuilder
from cogency.tools.shell import Shell
from tests.conftest import MockLLM


@pytest.mark.asyncio
async def test_defaults():
    agent = AgentBuilder("test_agent").with_llm(MockLLM()).build()
    executor = await agent._get_executor()

    assert executor.llm is not None
    assert executor.memory is None

    tool_names = [tool.name for tool in executor.tools]
    assert "shell" in tool_names


@pytest.mark.asyncio
async def test_no_memory():
    agent = AgentBuilder("test").with_llm(MockLLM()).build()
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
        agent = AgentBuilder("test").with_llm(MockLLM()).with_tools([Shell()]).with_memory().build()
    else:
        agent = AgentBuilder("test").with_llm(MockLLM()).with_tools([Shell()]).build()

    executor = await agent._get_executor()
    tool_names = [tool.name for tool in executor.tools]
    for tool in expected_tools:
        assert tool in tool_names
    assert len(tool_names) == len(expected_tools)


@pytest.mark.asyncio
async def test_config_setup():
    agent = AgentBuilder("test").with_llm(MockLLM()).robust().observe().persist().build()
    executor = await agent._get_executor()

    assert executor.config.robust is not None
    assert executor.config.observe is not None
    assert executor.config.persist is not None


@pytest.mark.asyncio
async def test_config_custom():
    agent = (
        AgentBuilder("test")
        .with_llm(MockLLM())
        .robust(attempts=5)
        .observe(metrics=False)
        .persist()
        .build()
    )
    executor = await agent._get_executor()

    assert executor.config.robust.attempts == 5
    assert executor.config.observe.metrics is False
    assert executor.config.persist.enabled is True


@pytest.mark.asyncio
async def test_mode_assignment():
    agent = AgentBuilder("test").with_llm(MockLLM()).fast_mode().with_depth(5).build()
    executor = await agent._get_executor()

    assert executor.mode == "fast"
    assert executor.depth == 5


@pytest.mark.asyncio
async def test_identity():
    agent = AgentBuilder("test").with_llm(MockLLM()).with_identity("helpful assistant").build()
    executor = await agent._get_executor()

    assert executor.identity == "helpful assistant"


@pytest.mark.asyncio
async def test_output_schema():
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}
    agent = AgentBuilder("test").with_llm(MockLLM()).with_schema(schema).build()
    executor = await agent._get_executor()

    assert executor.output_schema == schema


@pytest.mark.asyncio
async def test_run():
    agent = AgentBuilder("test").with_llm(MockLLM()).build()

    with patch("cogency.steps.execution.run_agent", new_callable=AsyncMock) as mock_run_agent:
        mock_run_agent.return_value = "Final Answer"
        result = await agent.run("test query")

        mock_run_agent.assert_called_once()
        assert result is not None


@pytest.mark.asyncio
async def test_run_error():
    agent = AgentBuilder("test").with_llm(MockLLM()).build()

    with patch("cogency.steps.execution.run_agent", side_effect=Exception("Test error")):
        try:
            await agent.run("test query")
            raise AssertionError("Should have raised exception")
        except Exception as e:
            assert "Test error" in str(e)


@pytest.mark.asyncio
async def test_stream():
    agent = AgentBuilder("test").with_llm(MockLLM()).build()

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


def test_traces_empty():
    agent = AgentBuilder("test").with_llm(MockLLM()).build()
    assert agent.traces() == []


@pytest.mark.asyncio
async def test_setup_notifier():
    agent = AgentBuilder("test").with_llm(MockLLM()).build()
    executor = await agent._get_executor()

    notifier = executor._setup_notifier()
    assert notifier is not None
    assert callable(notifier)
    assert hasattr(notifier, "emit")
    assert hasattr(notifier, "notifications")
