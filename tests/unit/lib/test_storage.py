"""Storage tests - SQLite persistence layer coverage."""

import tempfile
from pathlib import Path

import pytest

from cogency.lib.storage import (
    clear_messages,
    get_cogency_dir,
    get_db_path,
    load_messages,
    load_profile,
    save_message,
    save_profile,
)


@pytest.fixture
def temp_dir():
    """Temporary directory for test databases."""
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


def test_cogency_dir_default():
    """Cogency directory uses home by default."""
    cogency_dir = get_cogency_dir()
    assert cogency_dir == Path.home() / ".cogency"


def test_cogency_dir_custom(temp_dir):
    """Cogency directory uses custom base."""
    cogency_dir = get_cogency_dir(temp_dir)
    assert cogency_dir == Path(temp_dir)
    assert cogency_dir.exists()


def test_db_path(temp_dir):
    """Database path construction."""
    db_path = get_db_path(temp_dir)
    assert db_path == Path(temp_dir) / "store.db"


def test_save_load_single_message(temp_dir):
    """Save and load single conversation message."""
    conversation_id = "test_conv"

    # Save message
    success = save_message(conversation_id, "test_user", "user", "Hello", temp_dir)
    assert success is True

    # Load messages
    messages = load_messages(conversation_id, temp_dir)
    assert len(messages) == 1
    assert messages[0]["type"] == "user"
    assert messages[0]["content"] == "Hello"


def test_save_load_multiple_messages(temp_dir):
    """Save and load conversation with multiple messages."""
    conversation_id = "test_conv"

    # Save multiple messages
    assert save_message(conversation_id, "test_user", "user", "Hello", temp_dir)
    assert save_message(conversation_id, "test_user", "assistant", "Hi there", temp_dir)
    assert save_message(conversation_id, "test_user", "user", "How are you?", temp_dir)

    # Load all messages
    messages = load_messages(conversation_id, temp_dir)
    assert len(messages) == 3
    assert messages[0]["content"] == "Hello"
    assert messages[1]["content"] == "Hi there"
    assert messages[2]["content"] == "How are you?"


def test_load_messages_filtering_include(temp_dir):
    """Load messages with include filter."""
    conversation_id = "test_conv"

    # Save different message types
    assert save_message(conversation_id, "test_user", "user", "User message", temp_dir)
    assert save_message(conversation_id, "test_user", "assistant", "Assistant message", temp_dir)
    assert save_message(conversation_id, "test_user", "thinking", "Internal thought", temp_dir)

    # Load only user messages
    messages = load_messages(conversation_id, temp_dir, include=["user"])
    assert len(messages) == 1
    assert messages[0]["type"] == "user"
    assert messages[0]["content"] == "User message"


def test_load_messages_filtering_exclude(temp_dir):
    """Load messages with exclude filter."""
    conversation_id = "test_conv"

    # Save different message types
    assert save_message(conversation_id, "test_user", "user", "User message", temp_dir)
    assert save_message(conversation_id, "test_user", "assistant", "Assistant message", temp_dir)
    assert save_message(conversation_id, "test_user", "thinking", "Internal thought", temp_dir)

    # Load excluding thinking
    messages = load_messages(conversation_id, temp_dir, exclude=["thinking"])
    assert len(messages) == 2
    assert all(msg["type"] != "thinking" for msg in messages)


def test_load_messages_empty_conversation(temp_dir):
    """Load messages from non-existent conversation."""
    messages = load_messages("nonexistent", temp_dir)
    assert messages == []


def test_save_load_profile(temp_dir):
    """Save and load user profile."""
    user_id = "test_user"
    profile_data = {"preferences": "Python", "skill_level": "expert"}

    # Save profile
    success = save_profile(user_id, profile_data, temp_dir)
    assert success is True

    # Load profile
    loaded_profile = load_profile(user_id, temp_dir)
    assert loaded_profile == profile_data


def test_load_profile_nonexistent(temp_dir):
    """Fetch profile for non-existent user."""
    profile = load_profile("nonexistent", temp_dir)
    assert profile == {}


def test_save_profile_versioning(temp_dir):
    """Save profile creates new versions."""
    user_id = "test_user"

    # Save initial profile
    initial_profile = {"setting": "old_value"}
    assert save_profile(user_id, initial_profile, temp_dir)

    # Save updated profile
    new_profile = {"setting": "new_value", "additional": "data"}
    assert save_profile(user_id, new_profile, temp_dir)

    # Load and verify latest version
    loaded_profile = load_profile(user_id, temp_dir)
    assert loaded_profile == new_profile
    assert loaded_profile != initial_profile


def test_clear_messages(temp_dir):
    """Clear conversation messages."""
    conversation_id = "test_conv"

    # Save messages
    assert save_message(conversation_id, "test_user", "user", "Message 1", temp_dir)
    assert save_message(conversation_id, "test_user", "user", "Message 2", temp_dir)

    # Verify messages exist
    messages = load_messages(conversation_id, temp_dir)
    assert len(messages) == 2

    # Clear messages
    success = clear_messages(conversation_id, temp_dir)
    assert success is True

    # Verify messages cleared
    messages = load_messages(conversation_id, temp_dir)
    assert messages == []


def test_clear_messages_nonexistent(temp_dir):
    """Clear non-existent conversation."""
    success = clear_messages("nonexistent", temp_dir)
    assert success is True  # Should succeed even if conversation doesn't exist


def test_conversation_isolation(temp_dir):
    """Different conversations are isolated."""
    conv1_id = "conv_1"
    conv2_id = "conv_2"

    # Save to different conversations
    assert save_message(conv1_id, "user1", "user", "Conv 1 message", temp_dir)
    assert save_message(conv2_id, "user2", "user", "Conv 2 message", temp_dir)

    # Load each conversation
    conv1_messages = load_messages(conv1_id, temp_dir)
    conv2_messages = load_messages(conv2_id, temp_dir)

    assert len(conv1_messages) == 1
    assert len(conv2_messages) == 1
    assert conv1_messages[0]["content"] == "Conv 1 message"
    assert conv2_messages[0]["content"] == "Conv 2 message"

    # Clear one conversation shouldn't affect other
    assert clear_messages(conv1_id, temp_dir)
    conv1_messages = load_messages(conv1_id, temp_dir)
    conv2_messages = load_messages(conv2_id, temp_dir)

    assert conv1_messages == []
    assert len(conv2_messages) == 1


def test_profile_with_embedded_metadata(temp_dir):
    """Profile can contain embedded metadata."""
    user_id = "test_user"
    profile = {
        "who": "Python developer",
        "style": "clean, minimal",
        "_meta": {"last_learned_at": 1234567890.0, "messages_processed": 42},
    }

    # Save profile with embedded metadata
    success = save_profile(user_id, profile, temp_dir)
    assert success is True

    # Load profile with embedded metadata
    loaded_profile = load_profile(user_id, temp_dir)
    assert loaded_profile["who"] == "Python developer"
    assert loaded_profile["style"] == "clean, minimal"
    assert loaded_profile["_meta"]["last_learned_at"] == 1234567890.0
    assert loaded_profile["_meta"]["messages_processed"] == 42
