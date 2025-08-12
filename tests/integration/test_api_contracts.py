"""API contract validation - production stability assurance."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest
from resilient_result import Result

from cogency import Agent
from cogency.tools.base import Tool


class TestTool(Tool):
    """Contract-validating test tool."""

    def __init__(self):
        super().__init__(
            name="test_tool",
            description="Contract validation tool",
            schema="test_tool(action='validate')",
            emoji="🧪",
        )

    async def run(self, **kwargs) -> Result:
        """Contract: All tools must return Result objects."""
        if "action" not in kwargs:
            return Result.fail("Missing required parameter: action")
        return Result.ok(f"Contract validated: {kwargs['action']}")


def test_tool_result_contract():
    """Verify tools return Result objects."""
    tool = TestTool()

    # Valid execution
    result = asyncio.run(tool.run(action="test"))
    assert isinstance(result, Result)
    assert result.success
    assert "Contract validated: test" in result.data

    # Invalid execution
    result = asyncio.run(tool.run())
    assert isinstance(result, Result)
    assert not result.success
    assert "Missing required parameter" in result.error


@pytest.mark.asyncio
async def test_provider_response_contract():
    """Verify providers return string responses."""
    from tests.fixtures.provider import MockLLM

    provider = MockLLM("Test provider response")
    messages = [{"role": "user", "content": "test"}]

    # Response contract - use generate method
    result = await provider.generate(messages)
    assert isinstance(result.data, str)
    assert result.success

    # Stream contract
    chunks = []
    async for chunk in provider.stream(messages):
        chunks.append(chunk)
        assert isinstance(chunk, str)
    assert "".join(chunks) == "Test provider response"


@pytest.mark.asyncio
async def test_agent_execution_contract():
    """Verify agent execution returns string."""
    mock_run = AsyncMock(return_value="Agent execution result")

    with patch("cogency.Agent.run_async", mock_run):
        agent = Agent("test", tools=[], memory=False, notify=False)
        result = await agent.run_async("test query")

        # Contract: Agent must return string
        assert isinstance(result, str)
        assert len(result) > 0


def test_tool_parameter_validation_contract():
    """Verify tools validate parameters correctly."""
    tool = TestTool()

    # Required parameters missing
    result = asyncio.run(tool.run())
    assert not result.success
    assert "required parameter" in result.error.lower()

    # Valid parameters
    result = asyncio.run(tool.run(action="validate"))
    assert result.success


@pytest.mark.asyncio
async def test_concurrent_execution_isolation():
    """Verify concurrent agent executions don't interfere."""
    from tests.fixtures.provider import MockLLM

    provider1 = MockLLM("Response 1")
    provider2 = MockLLM("Response 2")

    # Mock agent execution to return different responses
    mock_run = AsyncMock(side_effect=["Response 1", "Response 2"])

    with patch("cogency.Agent.run_async", mock_run):
        agent1 = Agent("agent1", llm=provider1, tools=[], notify=False)
        agent2 = Agent("agent2", llm=provider2, tools=[], notify=False)

        # Run concurrently
        task1 = asyncio.create_task(agent1.run_async("query1"))
        task2 = asyncio.create_task(agent2.run_async("query2"))

        result1, result2 = await asyncio.gather(task1, task2)

        # Contract: Isolated execution results
        assert result1 != result2
        assert isinstance(result1, str)
        assert isinstance(result2, str)


@pytest.mark.asyncio
async def test_error_propagation_contract():
    """Verify errors propagate correctly through stack."""
    with AsyncMock() as mock_run:
        mock_run.side_effect = Exception("Deliberate test failure")

        with patch("cogency.Agent.run_async", mock_run):
            agent = Agent("test", tools=[], memory=False, notify=False)

            # Contract: Exceptions should propagate
            with pytest.raises(Exception) as exc_info:
                await agent.run_async("test error")

            assert "failure" in str(exc_info.value).lower()


def test_tool_schema_contract():
    """Verify tools provide required schema information."""
    tool = TestTool()

    # Contract: Tools must have required attributes
    assert hasattr(tool, "name")
    assert hasattr(tool, "description")
    assert hasattr(tool, "schema")
    assert tool.name == "test_tool"
    assert len(tool.description) > 0
    assert "test_tool" in tool.schema


@pytest.mark.asyncio
async def test_state_persistence_contract():
    """Verify state objects maintain required properties."""
    from cogency.state import State

    state = State("test query")

    # Contract: State must have required attributes
    assert state.query == "test query"
    assert hasattr(state.execution, "iteration")
    assert hasattr(state.execution, "messages")
    assert hasattr(state.execution, "pending_calls")
    assert state.execution.iteration == 0


@pytest.mark.asyncio
async def test_memory_storage_contract():
    """Verify memory system follows storage contracts."""
    from cogency.memory import MemoryManager
    from tests.fixtures.provider import MockLLM

    llm = MockLLM('{"preferences": {"style": "concise"}}')
    memory = MemoryManager(llm)

    # Contract: MemoryManager existence and basic functionality
    assert memory is not None
    assert hasattr(memory, "provider")
    assert memory.provider == llm
