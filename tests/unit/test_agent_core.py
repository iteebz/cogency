"""Test the main Agent class and its configuration."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent
from cogency.tools.calculator import Calculator
from tests.conftest import MockLLM


class TestAgentInitialization:
    """Test the pragmatic setup of the Agent class."""

    def test_agent_defaults(self):
        """Agent should have sane defaults: memory, default tools, etc."""
        agent = Agent("test_agent", llm=MockLLM())

        assert agent.flow is not None
        assert agent.flow.memory is not None, "Memory should be enabled by default"

        # Check for default tools + recall
        tool_names = [tool.name for tool in agent.flow.tools]
        assert "recall" in tool_names, "Recall tool should be present when memory is enabled"
        assert "calculator" in tool_names, "Default tools should be loaded"

    def test_agent_memory_disabled(self):
        """Agent with memory=False should not have memory or recall tool."""
        agent = Agent("test", llm=MockLLM(), memory=False)

        assert agent.flow.memory is None, "Memory should be disabled"

        tool_names = [tool.name for tool in agent.flow.tools]
        assert (
            "recall" not in tool_names
        ), "Recall tool should not be present when memory is disabled"

    @pytest.mark.parametrize(
        "memory_enabled,expected_tools",
        [
            (False, ["calculator"]),  # Just custom tools
            (True, ["calculator", "recall"]),  # Custom tools + recall
        ],
    )
    def test_agent_with_custom_tools(self, memory_enabled, expected_tools):
        """Agent should correctly handle custom tool lists with or without memory."""
        agent = Agent("test", llm=MockLLM(), tools=[Calculator()], memory=memory_enabled)

        tool_names = [tool.name for tool in agent.flow.tools]

        # Check that all expected tools are present
        for tool in expected_tools:
            assert tool in tool_names

        # Check that we have exactly the expected number of tools
        assert len(tool_names) == len(expected_tools)


@pytest.mark.asyncio
async def test_run_invokes_flow():
    """Ensure Agent.run() is a clean entrypoint to Flow.execute()."""
    agent = Agent("test", llm=MockLLM())

    # Patch the actual execution engine to keep the test focused and fast.
    # We don't need to test the full flow here, just that the Agent class
    # correctly invokes it.
    with patch.object(agent.flow.flow, "ainvoke", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = "Final Answer"

        result = await agent.run("test query")

        # Verify the agent called flow execution with arguments
        mock_execute.assert_called_once()

        # Verify we get some result back
        assert result is not None


@pytest.mark.asyncio
async def test_stream_validation():
    """Test that stream() handles empty and overly long queries."""
    agent = Agent("test", llm=MockLLM())

    with patch.object(agent.flow.flow, "ainvoke", new_callable=AsyncMock) as mock_execute:
        # Test empty query
        chunks = [chunk async for chunk in agent.stream("")]
        assert "Empty query not allowed" in chunks[0]
        mock_execute.assert_not_called()  # ainvoke should not be called for invalid input
        mock_execute.reset_mock()

        # Test query too long
        long_query = "a" * 10001
        chunks = [chunk async for chunk in agent.stream(long_query)]
        assert "Query too long" in chunks[0]
        mock_execute.assert_not_called()  # ainvoke should not be called for invalid input
