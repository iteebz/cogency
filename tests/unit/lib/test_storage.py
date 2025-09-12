import tempfile
from pathlib import Path

import pytest

from cogency.lib.storage import (
    Paths,
    clear_messages,
    get_cogency_dir,
    load_messages,
    load_profile,
    save_message,
    save_profile,
)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp:
        yield tmp


@pytest.mark.asyncio
async def test_storage_layer_behavior(temp_dir):
    """Storage layer persists conversations and profiles with filtering and isolation."""

    # Path configuration
    assert get_cogency_dir() == Path(".cogency")
    assert get_cogency_dir(temp_dir) == Path(temp_dir)
    assert Paths.db(base_dir=temp_dir) == Path(temp_dir) / "store.db"

    # Conversation persistence and filtering
    conv_id = "test_conv"

    # Multiple message types saved in order
    assert await save_message(conv_id, "user", "user", "Hello", temp_dir)
    assert await save_message(conv_id, "user", "assistant", "Hi there", temp_dir)
    assert await save_message(conv_id, "user", "thinking", "Internal thought", temp_dir)
    assert await save_message(conv_id, "user", "user", "How are you?", temp_dir)

    # All messages loaded in chronological order
    all_messages = load_messages(conv_id, temp_dir)
    assert len(all_messages) == 4
    assert [m["content"] for m in all_messages] == [
        "Hello",
        "Hi there",
        "Internal thought",
        "How are you?",
    ]

    # Filtering by include/exclude
    user_only = load_messages(conv_id, temp_dir, include=["user"])
    assert len(user_only) == 2
    assert all(m["type"] == "user" for m in user_only)

    no_thinking = load_messages(conv_id, temp_dir, exclude=["thinking"])
    assert len(no_thinking) == 3
    assert all(m["type"] != "thinking" for m in no_thinking)

    # Conversation isolation
    conv2_id = "other_conv"
    assert await save_message(conv2_id, "user2", "user", "Isolated message", temp_dir)

    conv1_msgs = load_messages(conv_id, temp_dir)
    conv2_msgs = load_messages(conv2_id, temp_dir)
    assert len(conv1_msgs) == 4
    assert len(conv2_msgs) == 1
    assert conv2_msgs[0]["content"] == "Isolated message"

    # Conversation clearing preserves isolation
    assert clear_messages(conv_id, temp_dir)
    assert load_messages(conv_id, temp_dir) == []
    assert len(load_messages(conv2_id, temp_dir)) == 1  # Other conversation unchanged

    # Profile versioning and metadata
    user_id = "test_user"
    initial_profile = {"setting": "old_value"}
    assert save_profile(user_id, initial_profile, temp_dir)

    updated_profile = {
        "setting": "new_value",
        "who": "Developer",
        "_meta": {"last_learned_at": 1234567890.0, "messages": 42},
    }
    assert save_profile(user_id, updated_profile, temp_dir)

    # Latest version loaded with all metadata preserved
    loaded = load_profile(user_id, temp_dir)
    assert loaded == updated_profile
    assert loaded["setting"] == "new_value"
    assert loaded["_meta"]["messages"] == 42

    # Non-existent data returns empty/success states
    assert load_messages("nonexistent", temp_dir) == []
    assert load_profile("nonexistent", temp_dir) == {}
    assert clear_messages("nonexistent", temp_dir) is True
