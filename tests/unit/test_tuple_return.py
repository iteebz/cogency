"""Test tuple return pattern prevents CLI memory regression."""

import pytest

from cogency import Agent


@pytest.fixture
def agent():
    """Agent with memory disabled for fast tests."""
    return Agent("test", memory=False)


@pytest.mark.asyncio
async def test_returns_tuple(agent):
    """run() returns (response, conversation_id)."""
    result = await agent.run("test")

    assert isinstance(result, tuple)
    assert len(result) == 2

    response, conv_id = result
    assert isinstance(response, str)
    assert isinstance(conv_id, str)
    assert len(conv_id) > 0


@pytest.mark.asyncio
async def test_conversation_continuity(agent):
    """Conversation_id enables continuity across calls."""
    # First call - new conversation
    response1, conv_id1 = await agent.run("Hello")

    # Second call - continue conversation
    response2, conv_id2 = await agent.run("What did I just say?", conversation_id=conv_id1)

    # Same conversation maintained
    assert conv_id1 == conv_id2
    assert isinstance(response2, str)


def test_run_sync_returns_tuple(agent):
    """run_sync() returns identical tuple pattern."""
    result = agent.run_sync("test")

    assert isinstance(result, tuple)
    assert len(result) == 2

    response, conv_id = result
    assert isinstance(response, str)
    assert isinstance(conv_id, str)
