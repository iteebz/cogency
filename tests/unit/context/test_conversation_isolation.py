"""Test conversation isolation to prevent cross-contamination."""

import pytest

from cogency.context.conversation import conversation


@pytest.fixture(autouse=True)
def clear_conversation_storage():
    """Clear conversation storage before and after each test."""
    import json
    from pathlib import Path

    # Get the conversations directory
    cogency_dir = Path.home() / ".cogency"
    conv_dir = cogency_dir / "conversations"

    def clear_test_files():
        """Clear all test-related conversation files."""
        if not conv_dir.exists():
            return

        # Pattern matches for test files
        patterns = ["user1", "user2", "eval_reasoning_"]

        for conv_file in conv_dir.glob("*.json"):
            if any(conv_file.stem.startswith(pattern) for pattern in patterns):
                try:
                    # Write empty array instead of deleting to avoid file creation issues
                    with open(conv_file, "w") as f:
                        json.dump([], f)
                except Exception:
                    pass

    # Clear before test
    clear_test_files()
    yield
    # Clear after test
    clear_test_files()


def test_conversation_isolation():
    """Conversations should be isolated - loading one shouldn't return messages from another."""

    # Add messages to first conversation
    conv1_id = "user1_1234567890"
    conversation.add(conv1_id, "user", "First conversation message")
    conversation.add(conv1_id, "assistant", "First response")

    # Add messages to second conversation (same user, different timestamp)
    conv2_id = "user1_1234567891"
    conversation.add(conv2_id, "user", "Second conversation message")
    conversation.add(conv2_id, "assistant", "Second response")

    # Loading conv1 should NOT return conv2 messages
    conv1_messages = conversation.messages(conv1_id)
    conv2_messages = conversation.messages(conv2_id)

    # Each conversation should only contain its own messages
    assert len(conv1_messages) == 2, f"Conv1 should have 2 messages, got {len(conv1_messages)}"
    assert len(conv2_messages) == 2, f"Conv2 should have 2 messages, got {len(conv2_messages)}"

    # Verify content isolation
    conv1_content = [msg["content"] for msg in conv1_messages]
    conv2_content = [msg["content"] for msg in conv2_messages]

    assert "First conversation message" in conv1_content
    assert "Second conversation message" not in conv1_content
    assert "Second conversation message" in conv2_content
    assert "First conversation message" not in conv2_content


def test_different_users_isolated():
    """Different users should have completely isolated conversations."""

    conv_user1 = "user1_1000000000"
    conv_user2 = "user2_1000000000"

    conversation.add(conv_user1, "user", "User1 message")
    conversation.add(conv_user2, "user", "User2 message")

    user1_messages = conversation.messages(conv_user1)
    user2_messages = conversation.messages(conv_user2)

    # Each user should only see their own messages
    user1_content = [msg["content"] for msg in user1_messages]
    user2_content = [msg["content"] for msg in user2_messages]

    assert "User1 message" in user1_content
    assert "User2 message" not in user1_content
    assert "User2 message" in user2_content
    assert "User1 message" not in user2_content


def test_evaluation_isolation_simulation():
    """Simulate evaluation scenario to ensure no cross-contamination."""

    # Simulate multiple evaluation tests
    test_conversations = [f"eval_reasoning_{i:02d}_{1000000000 + i}" for i in range(3)]

    # Each test adds its own messages
    for i, conv_id in enumerate(test_conversations):
        conversation.add(conv_id, "user", f"Test {i} prompt")
        conversation.add(conv_id, "assistant", f"Test {i} response")

    # Each conversation should be isolated
    for i, conv_id in enumerate(test_conversations):
        messages = conversation.messages(conv_id)
        assert len(messages) == 2, f"Test {i} should have exactly 2 messages"

        content = [msg["content"] for msg in messages]
        assert f"Test {i} prompt" in content

        # Should NOT contain messages from other tests
        for j in range(3):
            if i != j:
                assert f"Test {j} prompt" not in content
