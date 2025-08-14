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

    agent = Agent()
    resp = await agent("Hello", user_id="test")

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

    agent = Agent()
    resp = await agent("Test", user_id="test")
    assert isinstance(resp, str)
    assert len(resp) > 0
