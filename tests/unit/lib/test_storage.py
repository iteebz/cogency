"""SQLite storage layer tests - ACID properties and conversation isolation."""

import tempfile
from pathlib import Path

import pytest

from cogency.lib.paths import Paths, get_cogency_dir
from cogency.lib.storage import SQLite, clear_messages


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.mark.asyncio
async def test_storage_layer_behavior(temp_dir):
    """Storage layer persists conversations and profiles with filtering and isolation."""
    storage = SQLite(temp_dir)

    # Path configuration
    assert get_cogency_dir() == Path(".cogency")
    assert get_cogency_dir(temp_dir) == Path(temp_dir)
    assert Paths.db(base_dir=temp_dir) == Path(temp_dir) / "store.db"

    # Conversation persistence and filtering
    conv_id = "test_conv"

    # Multiple message types saved in order
    await storage.save_message(conv_id, "user", "user", "Hello")
    await storage.save_message(conv_id, "user", "assistant", "Hi there")
    await storage.save_message(conv_id, "user", "thinking", "Internal thought")
    await storage.save_message(conv_id, "user", "user", "How are you?")

    # All messages loaded in chronological order
    all_messages = await storage.load_messages(conv_id)
    assert len(all_messages) == 4
    assert [m["content"] for m in all_messages] == [
        "Hello",
        "Hi there",
        "Internal thought",
        "How are you?",
    ]

    # Filtering by include/exclude
    user_only = await storage.load_messages(conv_id, include=["user"])
    assert len(user_only) == 2
    assert all(m["type"] == "user" for m in user_only)

    no_thinking = await storage.load_messages(conv_id, exclude=["thinking"])
    assert len(no_thinking) == 3
    assert all(m["type"] != "thinking" for m in no_thinking)

    # Conversation isolation
    conv2_id = "other_conv"
    await storage.save_message(conv2_id, "user2", "user", "Isolated message")

    conv1_msgs = await storage.load_messages(conv_id)
    conv2_msgs = await storage.load_messages(conv2_id)
    assert len(conv1_msgs) == 4
    assert len(conv2_msgs) == 1
    assert conv2_msgs[0]["content"] == "Isolated message"

    # Conversation clearing preserves isolation
    clear_messages(conv_id, temp_dir)
    assert await storage.load_messages(conv_id) == []
    assert len(await storage.load_messages(conv2_id)) == 1  # Other conversation unchanged

    # Profile versioning and metadata
    user_id = "test_user"
    initial_profile = {"setting": "old_value"}
    await storage.save_profile(user_id, initial_profile)

    updated_profile = {
        "setting": "new_value",
        "who": "Developer",
        "_meta": {"last_learned_at": 1234567890.0, "messages": 42},
    }
    await storage.save_profile(user_id, updated_profile)

    # Latest version loaded with all metadata preserved
    loaded = await storage.load_profile(user_id)
    assert loaded == updated_profile
    assert loaded["setting"] == "new_value"
    assert loaded["_meta"]["messages"] == 42

    # Non-existent data returns empty/success states
    assert await storage.load_messages("nonexistent") == []
    assert await storage.load_profile("nonexistent") == {}
    clear_messages("nonexistent", temp_dir)  # Should not fail
