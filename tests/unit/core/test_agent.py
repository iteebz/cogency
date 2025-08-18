"""Agent tests."""

import os
from unittest.mock import patch

import pytest

from cogency import Agent, AgentResult, Ok


def test_create():
    """Agent creation."""
    agent = Agent()
    assert agent is not None


@pytest.mark.asyncio
async def test_call():
    """Agent call returns AgentResult with extracted final answer."""
    from unittest.mock import AsyncMock, Mock

    # Mock provider
    mock_provider = Mock()
    mock_provider.generate = AsyncMock(return_value=Ok("Final answer: Hello there!"))

    with patch("cogency.core.agent.create_llm", return_value=mock_provider):
        agent = Agent()
        result = await agent("Hello")

        assert isinstance(result, AgentResult)
        assert isinstance(result.response, str)
        assert result.response == "Hello there!"  # Final answer extracted
        assert result.conversation_id.startswith("None_")
        assert len(result.conversation_id) > len("None_")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_call():
    """Integration test with real LLM."""
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    agent = Agent()
    result = await agent("Hello")

    assert isinstance(result, AgentResult)
    assert isinstance(result.response, str)
    assert len(result.response) > 0
    assert result.conversation_id is not None


@pytest.mark.asyncio
async def test_runtime_multitenancy():
    """Runtime multitenancy with keyword user_id."""
    from unittest.mock import AsyncMock, Mock

    mock_provider = Mock()
    mock_provider.generate = AsyncMock(return_value=Ok("Final answer: Hello user!"))

    with patch("cogency.core.agent.create_llm", return_value=mock_provider):
        agent = Agent()
        # Multiple users, same agent
        alice = await agent("Hello", user_id="alice")
        bob = await agent("Hello", user_id="bob")

        assert alice.conversation_id.startswith("alice_")
        assert bob.conversation_id.startswith("bob_")
        assert alice.response == "Hello user!"
        assert bob.response == "Hello user!"


@pytest.mark.asyncio
async def test_sacred_interface():
    """Sacred zero-ceremony interface preserved."""
    from unittest.mock import AsyncMock, Mock

    mock_provider = Mock()
    mock_provider.generate = AsyncMock(return_value=Ok("Final answer: Sacred!"))

    with patch("cogency.core.agent.create_llm", return_value=mock_provider):
        agent = Agent()
        result = await agent("What is 2+2?")

        assert isinstance(result, AgentResult)
        assert result.response == "Sacred!"
        assert result.conversation_id.startswith("None_")


@pytest.mark.asyncio
async def test_keyword_only_enforcement():
    """Keyword-only user_id parameter enforced."""
    agent = Agent()

    # This should raise TypeError - positional user_id not allowed
    with pytest.raises(TypeError):
        await agent("test", "user123")


def test_context():
    """Context injection."""
    from cogency.context import context

    ctx = context("test", "user")
    assert isinstance(ctx, str)


@pytest.mark.asyncio
async def test_persist():
    """Persistence graceful failure - AgentResult contract."""
    from unittest.mock import AsyncMock, Mock

    # Mock provider
    mock_provider = Mock()
    mock_provider.generate = AsyncMock(return_value=Ok("Final answer: Test complete!"))

    with patch("cogency.core.agent.create_llm", return_value=mock_provider):
        agent = Agent()
        result = await agent("Test", user_id="test")

        assert isinstance(result, AgentResult)
        assert isinstance(result.response, str)
        assert result.response == "Test complete!"  # Final answer extracted
        assert result.conversation_id.startswith("test_")


def test_tools_config():
    """Tools configuration."""
    from cogency.tools import BASIC_TOOLS

    # Default has tools
    agent = Agent()
    assert len(agent.tools) > 0
    assert set(agent.tools.keys()) == {t.name for t in BASIC_TOOLS}

    # Empty tools
    agent_empty = Agent(tools=[])
    assert len(agent_empty.tools) == 0

    # Custom tools
    agent_custom = Agent(tools=BASIC_TOOLS[:2])
    assert len(agent_custom.tools) == 2


def test_max_iterations():
    """Max iterations config."""
    agent = Agent(max_iterations=10)
    assert agent.max_iterations == 10


def test_tool_parsing():
    """Tool parsing logic."""
    Agent()

    # Test tool pattern matching
    import re

    match = re.search(r"USE:\s*(\w+)\((.*?)\)", "USE: read_file(path='test.txt')", re.IGNORECASE)
    assert match is not None
    assert match.group(1) == "read_file"
