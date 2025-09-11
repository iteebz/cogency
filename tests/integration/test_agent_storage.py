"""Agent-Storage integration tests - conversation persistence boundaries."""

import tempfile
from unittest.mock import patch

import pytest

from cogency import Agent
from cogency.lib.storage import SQLite, clear_messages, load_messages


@pytest.fixture
def temp_storage():
    """Use temporary directory for isolated storage tests."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


# Use conftest.mock_llm fixture


@pytest.mark.asyncio
async def test_conversation_persistence(temp_storage, mock_llm):
    """Agent conversations persist across instances."""

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        # First agent interaction
        storage = SQLite(temp_storage)
        agent1 = Agent(llm="gemini", storage=storage)
        await agent1("Hello there", user_id="user1")

        # Destroy agent
        del agent1

        # New agent should access same conversation
        Agent(llm="gemini", storage=storage)

        # Check that conversation was actually stored
        messages = load_messages("user1_session", base_dir=temp_storage)
        assert len(messages) >= 2  # At least user message + agent response

        # Should have user message
        user_messages = [m for m in messages if m["type"] == "user"]
        assert len(user_messages) >= 1
        assert "Hello there" in user_messages[0]["content"]

        # Should have agent response
        agent_messages = [m for m in messages if m["type"] == "respond"]
        assert len(agent_messages) >= 1


@pytest.mark.asyncio
async def test_user_isolation(temp_storage, mock_llm):
    """Different users have isolated conversations."""

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        storage = SQLite(temp_storage)
        agent = Agent(llm="gemini", storage=storage)

        # User 1 conversation
        await agent("User 1 message", user_id="user1")

        # User 2 conversation
        await agent("User 2 message", user_id="user2")

        # Check isolation
        user1_messages = load_messages("user1_session", base_dir=temp_storage)
        user2_messages = load_messages("user2_session", base_dir=temp_storage)

        # Each user should have their own messages
        user1_content = [m["content"] for m in user1_messages if m["type"] == "user"]
        user2_content = [m["content"] for m in user2_messages if m["type"] == "user"]

        assert "User 1 message" in user1_content[0]
        assert "User 2 message" in user2_content[0]

        # Messages should not cross-contaminate
        assert not any("User 2 message" in msg for msg in user1_content)
        assert not any("User 1 message" in msg for msg in user2_content)


@pytest.mark.asyncio
async def test_conversation_continuity(temp_storage, mock_llm):
    """Agent can continue previous conversations."""

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        storage = SQLite(temp_storage)
        agent = Agent(llm="gemini", storage=storage)

        # Initial conversation
        await agent("My name is Alice", user_id="user1")

        # Continue conversation (agent should have context)
        await agent("What did I just tell you?", user_id="user1")

        # Check conversation continuity in storage
        messages = load_messages("user1_session", base_dir=temp_storage)
        user_messages = [m for m in messages if m["type"] == "user"]

        assert len(user_messages) == 2
        assert "My name is Alice" in user_messages[0]["content"]
        assert "What did I just tell you?" in user_messages[1]["content"]


@pytest.mark.asyncio
async def test_storage_failure_graceful(temp_storage, mock_llm):
    """Agent handles storage failures gracefully."""

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        # Create agent with storage that will fail
        storage = SQLite(temp_storage)

        # Patch the record_message to fail
        with patch.object(storage, "record_message", side_effect=Exception("Storage failed")):
            agent = Agent(llm="gemini", storage=storage)

            # Should not crash on storage failure - just continue without recording
            response = await agent("Test message", user_id="user1")
            assert isinstance(response, str)
            assert len(response) > 0


@pytest.mark.asyncio
async def test_conversation_cleanup(temp_storage, mock_llm):
    """Storage cleanup works correctly."""

    with patch("cogency.lib.llms.Gemini", return_value=mock_llm):
        storage = SQLite(temp_storage)
        agent = Agent(llm="gemini", storage=storage)

        # Create conversation
        await agent("Test message", user_id="user1")

        # Verify messages exist
        messages = load_messages("user1_session", base_dir=temp_storage)
        assert len(messages) > 0

        # Clear conversation
        clear_messages("user1_session", base_dir=temp_storage)

        # Verify messages cleared
        messages_after = load_messages("user1_session", base_dir=temp_storage)
        assert len(messages_after) == 0
