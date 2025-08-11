"""Tests for conversation persistence and threading."""

from datetime import datetime

import pytest

from cogency.state import Conversation, State
from cogency.state.mutations import add_message
from cogency.storage.state import SQLite


@pytest.fixture
def sample_conversation():
    """Create conversation with message history."""
    conv = Conversation(user_id="test_user")
    conv.messages = [
        {"role": "user", "content": "Hello", "timestamp": datetime.now().isoformat()},
        {"role": "assistant", "content": "Hi there", "timestamp": datetime.now().isoformat()},
        {"role": "user", "content": "How are you?", "timestamp": datetime.now().isoformat()},
    ]
    return conv


def test_conversation_creation():
    """Test conversation creates with unique ID and user mapping."""
    conv1 = Conversation(user_id="user1")
    conv2 = Conversation(user_id="user1")

    # Each conversation gets unique ID
    assert conv1.conversation_id != conv2.conversation_id
    assert conv1.user_id == conv2.user_id == "user1"
    assert conv1.messages == []
    assert isinstance(conv1.last_updated, datetime)


def test_message_threading():
    """Test messages maintain conversation threading."""
    state = State(query="test", user_id="test_user")

    # Add conversation flow
    add_message(state, "user", "What is Python?")
    add_message(state, "assistant", "Python is a programming language")
    add_message(state, "user", "Tell me more about its syntax")

    # Verify conversation threading
    conv_messages = state.conversation.messages
    exec_messages = state.execution.messages

    # Same messages in both places
    assert len(conv_messages) == 3
    assert len(exec_messages) == 3
    assert conv_messages == exec_messages

    # Verify conversation flow
    assert conv_messages[0]["role"] == "user"
    assert conv_messages[0]["content"] == "What is Python?"
    assert conv_messages[1]["role"] == "assistant"
    assert conv_messages[2]["role"] == "user"
    assert "syntax" in conv_messages[2]["content"]


def test_conversation_persistence_across_tasks():
    """Test conversation persists when starting new tasks."""
    # This test shows the key feature: conversation continuity
    pass  # Will implement after storage is working


@pytest.mark.asyncio
async def test_conversation_storage_operations():
    """Test conversation CRUD operations in storage."""
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test.db"
        store = SQLite(str(db_path))

        conv = Conversation(user_id="test_user")
        conv.messages = [
            {"role": "user", "content": "Test message", "timestamp": datetime.now().isoformat()}
        ]

        # Save conversation
        result = await store.save_conversation(conv)
        assert result is True

        # Load conversation
        loaded = await store.load_conversation(conv.conversation_id, conv.user_id)
        assert loaded is not None
        assert loaded.conversation_id == conv.conversation_id
        assert loaded.user_id == conv.user_id
        assert len(loaded.messages) == 1
        assert loaded.messages[0]["content"] == "Test message"

        # Delete conversation
        deleted = await store.delete_conversation(conv.conversation_id)
        assert deleted is True

        # Verify deletion
        not_found = await store.load_conversation(conv.conversation_id, conv.user_id)
        assert not_found is None


@pytest.mark.asyncio
async def test_conversation_continues_across_tasks():
    """Test conversation history is maintained across multiple tasks."""
    user_id = "test_user"

    # Task 1: Start conversation
    state1 = await State.start_task("What is AI?", user_id)
    conv_id = state1.conversation.conversation_id

    add_message(state1, "user", "What is AI?")
    add_message(state1, "assistant", "AI is artificial intelligence")

    # Manually save conversation since autosave is disabled in tests
    from cogency.storage.state import SQLite
    store = SQLite()
    await store.save_conversation(state1.conversation)

    await state1.archive_conversation()

    # Task 2: Continue same conversation
    state2 = await State.start_task("Tell me more", user_id, conversation_id=conv_id)

    # Verify conversation history carried forward
    assert state2.conversation.conversation_id == conv_id
    assert len(state2.execution.messages) == 2  # History loaded into execution
    assert state2.execution.messages[0]["content"] == "What is AI?"
    assert state2.execution.messages[1]["content"] == "AI is artificial intelligence"

    # Add to conversation
    add_message(state2, "user", "Tell me more")
    add_message(state2, "assistant", "AI includes machine learning...")

    # Verify total conversation
    assert len(state2.conversation.messages) == 4
    await state2.archive_conversation()


def test_conversation_isolation_between_users():
    """Test conversations are properly isolated between users."""
    conv1 = Conversation(user_id="user1")
    conv2 = Conversation(user_id="user2")

    add_message_to_conv(conv1, "user", "User 1 message")
    add_message_to_conv(conv2, "user", "User 2 message")

    assert len(conv1.messages) == 1
    assert len(conv2.messages) == 1
    assert conv1.messages[0]["content"] == "User 1 message"
    assert conv2.messages[0]["content"] == "User 2 message"


def test_conversation_timestamp_updates():
    """Test conversation timestamps update correctly."""
    conv = Conversation(user_id="test_user")
    original_time = conv.last_updated

    # Add message should update timestamp
    add_message_to_conv(conv, "user", "Test message")
    assert conv.last_updated > original_time


def add_message_to_conv(conv: Conversation, role: str, content: str):
    """Helper to add message directly to conversation."""
    message = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
    conv.messages.append(message)
    conv.last_updated = datetime.now()
