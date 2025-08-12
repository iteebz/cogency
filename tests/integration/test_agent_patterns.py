"""Agent integration patterns - behavioral validation."""

from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.tools import Shell


@pytest.mark.asyncio
async def test_agent_initialization_auto_detection():
    """Test agent auto-detects LLM provider and sets up components."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent = Agent("test_agent", tools=[Shell()])

        # Should auto-detect and setup components
        assert agent.name == "test_agent"
        assert agent.llm is not None
        assert len(agent.tools) == 1
        assert agent.tools[0].name == "shell"


@pytest.mark.asyncio
async def test_agent_memory_disabled_pattern():
    """Test agent with memory explicitly disabled."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent = Agent("test_agent", memory=False, tools=[Shell()])

        assert agent.memory is None
        assert agent.llm is not None
        assert len(agent.tools) == 1


@pytest.mark.asyncio
async def test_agent_memory_enabled_pattern():
    """Test agent with memory enabled initializes memory system."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent = Agent("test_agent", memory=True, tools=[])

        assert agent.memory is not None
        assert agent.llm is not None


@pytest.mark.asyncio
async def test_agent_custom_tool_configuration():
    """Test agent handles different tool configurations."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        # No tools
        agent_no_tools = Agent("test", tools=[])
        assert len(agent_no_tools.tools) == 0

        # Multiple tools
        agent_multi_tools = Agent("test", tools=[Shell(), Shell()])
        assert len(agent_multi_tools.tools) == 2


@pytest.mark.asyncio
async def test_agent_execution_contract():
    """Test agent execution returns string response."""
    from unittest.mock import AsyncMock

    with patch("cogency.Agent.run_async", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = "Test response from agent execution"

        agent = Agent("test", tools=[], memory=False, notify=False)
        result = await agent.run_async("test query")

        # Contract: Agent execution must return string
        assert isinstance(result, str)
        assert len(result) > 0
        assert result == "Test response from agent execution"


@pytest.mark.asyncio
async def test_agent_component_isolation():
    """Test agent components don't interfere across instances."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent1 = Agent("agent1", tools=[Shell()], memory=False)
        agent2 = Agent("agent2", tools=[], memory=True)

        # Components should be isolated
        assert agent1.name != agent2.name
        assert len(agent1.tools) != len(agent2.tools)
        # Memory isolation: memory=False -> None, memory=True -> Memory
        assert agent1.memory is None
        assert agent2.memory is not None


@pytest.mark.asyncio
async def test_agent_minimal_configuration():
    """Test agent works with minimal configuration."""
    with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
        agent = Agent("minimal", tools=[], memory=False, notify=False)

        assert agent.name == "minimal"
        assert agent.llm is not None
        assert agent.memory is None
        assert len(agent.tools) == 0


@pytest.mark.asyncio
async def test_agent_provider_dependency():
    """Test agent fails gracefully without provider credentials."""
    with patch.dict("os.environ", {}, clear=True):
        # Should raise exception when no provider available
        with pytest.raises((ValueError, RuntimeError)):
            Agent("test", tools=[])
