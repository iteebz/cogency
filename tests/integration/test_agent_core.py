"""Core Agent integration: Agent → Provider → Response."""

import pytest

from cogency import Agent
from cogency.tools import Files


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_provider_integration():
    """Agent successfully coordinates with provider."""
    agent = Agent("test")

    # Test basic agent-provider coordination
    result = await agent.run("What is 2+2?")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert len(result[0]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_tools_integration():
    """Agent successfully uses tools."""
    agent = Agent("test", tools=[Files()])

    # Test agent-tools coordination
    result = await agent.run("List current directory")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], str)
    assert len(result[0]) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_agent_memory_integration():
    """Agent successfully uses memory."""
    agent = Agent("test", memory=True)

    # Test agent-memory coordination
    result1, conv_id = await agent.run("Remember: my name is test", user_id="user1")
    result2, _ = await agent.run("What's my name?", user_id="user1", conversation_id=conv_id)

    assert isinstance(result1, str)
    assert isinstance(result2, str)
    assert isinstance(conv_id, str)
