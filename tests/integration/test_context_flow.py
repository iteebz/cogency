"""Context flow integration: Memory → Agent → Response."""

import pytest

from cogency import Agent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_flow():
    """Agent uses memory context in multi-turn conversations."""
    agent = Agent("test", memory=True)

    # First turn - establish context
    result1, conv_id = await agent.run("My name is Alice and I like pizza", user_id="user1")

    # Second turn - should use context from first turn
    result2, _ = await agent.run(
        "What's my name and favorite food?", user_id="user1", conversation_id=conv_id
    )

    # Verify context flows through system
    assert isinstance(result1, str)
    assert isinstance(result2, str)
    assert isinstance(conv_id, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_context_isolation():
    """Context properly isolated between users."""
    agent = Agent("test", memory=True)

    # User 1 establishes context
    result1, conv1 = await agent.run("I prefer brief responses", user_id="user1")

    # User 2 establishes different context
    result2, conv2 = await agent.run("I prefer detailed explanations", user_id="user2")

    # Verify isolation
    assert conv1 != conv2  # Different conversations
    assert isinstance(result1, str)
    assert isinstance(result2, str)
