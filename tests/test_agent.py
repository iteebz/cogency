"""Agent tests."""

import pytest

from cogency import Agent


@pytest.mark.asyncio
async def test_call():
    import os

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    agent = Agent()
    resp = await agent("What is 2+2?")

    assert isinstance(resp, str)
    assert len(resp) > 0
    assert "4" in resp


@pytest.mark.asyncio
async def test_user_context():
    import os

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    agent = Agent()
    resp = await agent("Hello", user_id="test")

    assert isinstance(resp, str)
    assert len(resp) > 0


@pytest.mark.asyncio
async def test_persistence():
    import os

    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    agent = Agent()
    resp = await agent("Test", user_id="test")
    assert isinstance(resp, str)
    assert len(resp) > 0


@pytest.mark.asyncio
async def test_tool_integration():
    """Test agent with tools integration."""
    import os
    
    if not os.getenv("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    
    from cogency import BASIC_TOOLS
    agent = Agent(tools=BASIC_TOOLS)
    
    # Test that agent can execute without tools
    resp = await agent("What is 2+2?")
    assert isinstance(resp, str)
    assert len(resp) > 0


def test_configuration():
    """Test agent configuration."""
    agent = Agent(model="claude-4", verbose=True, max_iterations=10)
    
    assert agent.model == "claude-4"
    assert agent.verbose is True
    assert agent.max_iterations == 10
