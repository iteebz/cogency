"""State lifecycle integration: Creation → Persistence → Cleanup."""

import pytest

from cogency import Agent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_state_lifecycle():
    """State properly managed through agent execution lifecycle."""
    agent = Agent("test", memory=True)

    # Create state through agent interaction
    result, conv_id = await agent.run("Start a conversation", user_id="test")

    # State should persist for follow-up
    result2, conv_id2 = await agent.run(
        "Continue conversation", user_id="test", conversation_id=conv_id
    )

    # Verify state continuity
    assert conv_id == conv_id2  # Same conversation maintained
    assert isinstance(result, str)
    assert isinstance(result2, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_state_isolation():
    """State properly isolated between different users."""
    agent = Agent("test", memory=True)

    # User 1 creates state
    result1, conv1 = await agent.run("User 1 message", user_id="user1")

    # User 2 creates separate state
    result2, conv2 = await agent.run("User 2 message", user_id="user2")

    # Verify isolation
    assert conv1 != conv2  # Different states
    assert isinstance(result1, str)
    assert isinstance(result2, str)
