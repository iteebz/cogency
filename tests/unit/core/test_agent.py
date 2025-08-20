"""Agent tests."""

from unittest.mock import AsyncMock, patch

import pytest

from cogency import Agent, AgentResult, Ok


def test_create():
    """Agent creation."""
    agent = Agent()
    assert agent is not None


@pytest.mark.asyncio
async def test_call(mock_llm):
    """Agent call returns AgentResult with extracted final answer."""
    xml_response = """<thinking>
User said hello.
</thinking>

<response>
Hello there!
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        agent = Agent()
        result = await agent("Hello")

        assert isinstance(result, AgentResult)
        assert isinstance(result.response, str)
        assert "Hello there!" in result.response  # Response section extracted
        assert result.conversation_id.startswith("default_")
        assert len(result.conversation_id) > len("agent_")


@pytest.mark.asyncio
async def test_integration(mock_llm):
    """Integration test."""
    xml_response = """<thinking>
The user is greeting me with "Hello". I should respond politely.
</thinking>

<response>
Hello! How can I help you today?
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        # Test complete end-to-end flow
        agent = Agent()
        result = await agent("Hello")

        # Verify full pipeline works
        assert isinstance(result, AgentResult)
        assert isinstance(result.response, str)
        assert "Hello! How can I help you today?" in result.response
        assert result.conversation_id.startswith("default_")

        # Verify XML parsing worked
        assert "thinking" not in result.response.lower()  # Thinking stripped out

        # Verify LLM was called with proper message structure
        mock_llm.generate.assert_called_once()
        call_args = mock_llm.generate.call_args[0][0]
        assert isinstance(call_args, list)
        assert len(call_args) >= 1
        assert call_args[0]["role"] == "system"
        assert call_args[-1]["content"] == "Hello"


@pytest.mark.asyncio
async def test_multitenancy(mock_llm):
    """Runtime multitenancy."""
    xml_response = """<thinking>
User is greeting me.
</thinking>

<response>
Hello user!
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        agent = Agent()
        # Multiple users, same agent
        alice = await agent("Hello", user_id="alice")
        bob = await agent("Hello", user_id="bob")

        assert alice.conversation_id.startswith("alice_")
        assert bob.conversation_id.startswith("bob_")
        assert "Hello user!" in alice.response
        assert "Hello user!" in bob.response


@pytest.mark.asyncio
async def test_interface(mock_llm):
    """Zero-ceremony interface."""
    xml_response = """<thinking>
This is a math question.
</thinking>

<response>
Sacred!
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        agent = Agent()
        result = await agent("What is 2+2?")

        assert isinstance(result, AgentResult)
        assert "Sacred!" in result.response
        assert result.conversation_id.startswith("default_")


@pytest.mark.asyncio
async def test_keyword_only():
    """Keyword-only parameters."""
    agent = Agent()

    # This should raise TypeError - positional user_id not allowed
    with pytest.raises(TypeError):
        await agent("test", "user123")


def test_context():
    """Context injection."""
    from cogency.context import context

    ctx = context.assemble("test", "user", "conv1", "task1", {})
    assert isinstance(ctx, list)
    assert len(ctx) > 0
    assert all("role" in msg for msg in ctx)


@pytest.mark.asyncio
async def test_persist(mock_llm):
    """Persistence graceful failure - AgentResult contract."""
    xml_response = """<thinking>
This is a test.
</thinking>

<response>
Test complete!
</response>"""
    mock_llm.generate = AsyncMock(return_value=Ok(xml_response))

    with patch("cogency.core.agent.create_llm", return_value=mock_llm):
        agent = Agent()
        result = await agent("Test", user_id="test")

        assert isinstance(result, AgentResult)
        assert isinstance(result.response, str)
        assert "Test complete!" in result.response  # Response section extracted
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
