"""Storage layer tests - SQLite persistence operations."""

import tempfile

from cogency.lib.storage import (
    load_conversations,
    load_memory,
    save_conversation_message,
    save_memory,
)


def test_conversation_empty_load():
    """Empty conversation returns empty list."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = load_conversations("nonexistent_conv", temp_dir)
        assert isinstance(result, list)
        assert result == []


def test_conversation_roundtrip():
    """Conversation message save/load roundtrip."""
    with tempfile.TemporaryDirectory() as temp_dir:
        conv_id = "test_conversation"

        # Save messages
        assert save_conversation_message(conv_id, "user", "Hello", temp_dir)
        assert save_conversation_message(conv_id, "assistant", "Hi there", temp_dir)

        # Load and verify
        messages = load_conversations(conv_id, temp_dir)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[0]["content"] == "Hello"
        assert messages[1]["role"] == "assistant"
        assert messages[1]["content"] == "Hi there"


def test_memory_empty_load():
    """Empty memory returns empty dict."""
    with tempfile.TemporaryDirectory() as temp_dir:
        result = load_memory("nonexistent_user", temp_dir)
        assert isinstance(result, dict)
        assert result == {}


def test_memory_roundtrip():
    """Memory data save/load roundtrip."""
    with tempfile.TemporaryDirectory() as temp_dir:
        user_id = "test_user"
        test_data = {"key": "value", "count": 42, "items": ["a", "b", "c"]}

        # Save and load
        assert save_memory(user_id, test_data, temp_dir)
        loaded = load_memory(user_id, temp_dir)

        assert isinstance(loaded, dict)
        assert loaded == test_data


def test_memory_update():
    """Memory updates properly."""
    with tempfile.TemporaryDirectory() as temp_dir:
        user_id = "test_user"

        # Save initial data
        initial_data = {"version": 1}
        assert save_memory(user_id, initial_data, temp_dir)

        # Update with new data
        updated_data = {"version": 2, "new_field": "added"}
        assert save_memory(user_id, updated_data, temp_dir)

        # Verify update
        loaded = load_memory(user_id, temp_dir)
        assert loaded == updated_data
        assert loaded["version"] == 2
