"""Agent tests."""

import pytest

from cogency import Agent


def test_create():
    """Agent creation."""
    agent = Agent()
    assert agent is not None


@pytest.mark.asyncio
async def test_call():
    """Agent call."""
    import os

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    agent = Agent()
    resp = await agent("What is 2+2?")

    assert isinstance(resp, str)
    assert len(resp) > 0
    assert "4" in resp


@pytest.mark.asyncio
async def test_user():
    """Agent with user_id."""
    import os

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    agent = Agent(user_id="test")
    resp = await agent("Hello")

    assert isinstance(resp, str)
    assert len(resp) > 0


def test_context():
    """Context injection."""
    from cogency.context import context

    ctx = context("test", "user")
    assert isinstance(ctx, str)


@pytest.mark.asyncio
async def test_persist():
    """Persistence graceful failure."""
    import os

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    agent = Agent(user_id="test")
    resp = await agent("Test")
    assert isinstance(resp, str)
    assert len(resp) > 0


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
