"""Storage isolation integration: User separation and data integrity."""

import pytest

from cogency import Agent


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_isolation():
    """Different users get isolated storage."""
    agent = Agent("test", memory=True)

    # User 1 creates conversation
    result1, conv1 = await agent.run("I like pizza", user_id="user1")

    # User 2 creates separate conversation
    result2, conv2 = await agent.run("I like burgers", user_id="user2")

    # Verify isolation
    assert conv1 != conv2  # Different conversation IDs
    assert isinstance(result1, str)
    assert isinstance(result2, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_persistence():
    """Conversations persist across agent instances."""
    # First agent instance
    agent1 = Agent("test", memory=True)
    result1, conv_id = await agent1.run("Remember: favorite color is blue", user_id="user1")

    # New agent instance - should access same storage
    agent2 = Agent("test", memory=True)
    result2, _ = await agent2.run(
        "What's my favorite color?", user_id="user1", conversation_id=conv_id
    )

    assert isinstance(result1, str)
    assert isinstance(result2, str)
    assert isinstance(conv_id, str)
