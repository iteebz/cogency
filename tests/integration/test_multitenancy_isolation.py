"""Integration tests for multitenancy isolation and user_id scoping."""

import pytest

from cogency import Agent
from cogency.context.conversation import Conversation
from cogency.context.memory import Memory
from cogency.storage import Store


@pytest.mark.integration
@pytest.mark.asyncio
async def test_conversation_isolation():
    """Conversations are isolated by user_id."""
    store = Store()
    await store._ensure_schema()

    # Create conversations for different users
    user1_conv = Conversation(
        conversation_id="conv1",
        user_id="user1",
        messages=[{"role": "user", "content": "Python help"}],
    )

    user2_conv = Conversation(
        conversation_id="conv2",
        user_id="user2",
        messages=[{"role": "user", "content": "JavaScript help"}],
    )

    await store.save_conversation(user1_conv)
    await store.save_conversation(user2_conv)

    # Load as correct user - should succeed
    loaded_user1 = await store.load_conversation("conv1", "user1")
    assert loaded_user1 is not None
    assert loaded_user1.user_id == "user1"
    assert "Python" in loaded_user1.messages[0]["content"]

    loaded_user2 = await store.load_conversation("conv2", "user2")
    assert loaded_user2 is not None
    assert loaded_user2.user_id == "user2"
    assert "JavaScript" in loaded_user2.messages[0]["content"]

    # Cross-user access should fail
    cross_access1 = await store.load_conversation("conv1", "user2")
    assert cross_access1 is None

    cross_access2 = await store.load_conversation("conv2", "user1")
    assert cross_access2 is None


# Deleted: test_workspace_isolation - tests deleted Workspace functionality


@pytest.mark.integration
@pytest.mark.asyncio
async def test_user_id_propagation():
    """Agent propagates user_id correctly."""
    agent = Agent("test", memory=False)

    # Should handle user_id parameter without crashing
    result, conversation_id = await agent.run("Simple query", user_id="test_user")
    assert isinstance(result, str)
    assert len(result) > 0
    assert isinstance(conversation_id, str)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_memory_scoping():
    """Memory handles user_id scoping."""
    memory = Memory()

    # Should handle user_id scoping without errors
    context = await memory.activate("test_user", {"query": "Test query"})
    assert isinstance(context, str)
