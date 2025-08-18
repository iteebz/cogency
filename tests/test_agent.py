"""Agent tests."""

import os
from unittest.mock import patch

import pytest

from cogency import Agent, AgentResult


def test_create():
    """Agent creation."""
    agent = Agent()
    assert agent is not None


@pytest.mark.asyncio
async def test_call():
    """Agent call returns AgentResult with extracted final answer."""
    with patch("cogency.core.agent.generate") as mock_generate:
        mock_generate.return_value = "Final answer: Hello there!"

        agent = Agent()
        result = await agent("Hello")

        assert isinstance(result, AgentResult)
        assert isinstance(result.response, str)
        assert result.response == "Hello there!"  # Final answer extracted
        assert result.conversation_id.startswith("default_")
        assert len(result.conversation_id) > len("default_")


@pytest.mark.integration
@pytest.mark.asyncio
async def test_integration_call():
    """Integration test with real LLM."""
    # Use actual API key for integration test
    os.environ["OPENAI_API_KEY"] = (
        "<REDACTED>"
    )

    agent = Agent()
    result = await agent("Hello")

    assert isinstance(result, AgentResult)
    assert isinstance(result.response, str)
    assert len(result.response) > 0
    assert result.conversation_id is not None


@pytest.mark.asyncio
async def test_user():
    """Agent with user_id returns AgentResult with correct conversation_id."""
    with patch("cogency.core.agent.generate") as mock_generate:
        mock_generate.return_value = "Final answer: Hello user!"

        agent = Agent(user_id="test")
        result = await agent("Hello")

        assert isinstance(result, AgentResult)
        assert isinstance(result.response, str)
        assert result.response == "Hello user!"  # Final answer extracted
        assert result.conversation_id.startswith("test_")


def test_context():
    """Context injection."""
    from cogency.context import context

    ctx = context("test", "user")
    assert isinstance(ctx, str)


@pytest.mark.asyncio
async def test_persist():
    """Persistence graceful failure - AgentResult contract."""
    with patch("cogency.core.agent.generate") as mock_generate:
        mock_generate.return_value = "Final answer: Test complete!"

        agent = Agent(user_id="test")
        result = await agent("Test")

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
