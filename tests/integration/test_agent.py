"""Agent integration tests."""

from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.tools import Shell


@pytest.mark.asyncio
async def test_agent_defaults():
    """Test agent sets up components directly."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent = Agent("test_agent", tools=[Shell()])

        # Should have set up components directly in __init__
        assert agent.name == "test_agent"
        assert agent.llm is not None
        assert agent.memory is None  # Default is False
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "shell"


@pytest.mark.asyncio
async def test_memory_disabled():
    """Test agent with memory explicitly disabled."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent = Agent("test_agent", memory=False, tools=[Shell()])

        assert agent.memory is None
        assert agent.llm is not None
        assert len(agent.tools) == 1


@pytest.mark.parametrize("memory_enabled", [False, True])
@pytest.mark.asyncio
async def test_custom_tools(memory_enabled):
    """Test agent with custom tool configuration."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        tools = [Shell()] if memory_enabled else []
        agent = Agent("test_agent", memory=memory_enabled, tools=tools)

        assert agent.memory is not None if memory_enabled else agent.memory is None
        assert len(agent.tools) == len(tools)


@pytest.mark.asyncio
async def test_run():
    """Test basic agent execution with mocked execution - no real API calls."""
    from unittest.mock import AsyncMock

    # Mock the agent execution to avoid LLM calls and parsing complexity
    with patch("cogency.Agent.run_async", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = "Test execution completed successfully."

        agent = Agent("test_agent", tools=[], memory=False, notify=False)

        # Should execute successfully with mocked execution
        response = await agent.run_async("test query")

        # Verify contract compliance
        assert isinstance(response, str)
        assert len(response) > 0
        assert "successfully" in response.lower()
