"""Test history_transform hook in context assembly."""

import pytest

from cogency.context.assembly import assemble


@pytest.mark.asyncio
async def test_history_transform_hook_called(mock_storage):
    """history_transform is called when provided."""
    storage = mock_storage
    conversation_id = "test_conv"
    user_id = "test_user"

    # Populate some history
    await storage.save_message(conversation_id, user_id, "user", "first message", 1.0)
    await storage.save_message(conversation_id, user_id, "respond", "first response", 2.0)
    await storage.save_message(conversation_id, user_id, "user", "second message", 3.0)
    await storage.save_message(conversation_id, user_id, "respond", "second response", 4.0)

    # Transform that reverses message order
    async def reverse_transform(messages: list[dict]) -> list[dict]:
        return list(reversed(messages))

    result = await assemble(
        user_id,
        conversation_id,
        tools=[],
        storage=storage,
        history_window=None,
        history_transform=reverse_transform,
        profile_enabled=False,
    )

    # System message + 4 conversation messages
    assert len(result) == 5
    assert result[0]["role"] == "system"

    # Messages should be reversed
    conv_messages = result[1:]
    assert conv_messages[0]["content"] == "second response"
    assert conv_messages[1]["content"] == "second message"
    assert conv_messages[2]["content"] == "first response"
    assert conv_messages[3]["content"] == "first message"


@pytest.mark.asyncio
async def test_history_transform_not_called_when_none(mock_storage):
    """history_transform=None preserves default behavior."""
    storage = mock_storage
    conversation_id = "test_conv"
    user_id = "test_user"

    await storage.save_message(conversation_id, user_id, "user", "first", 1.0)
    await storage.save_message(conversation_id, user_id, "respond", "second", 2.0)

    result = await assemble(
        user_id,
        conversation_id,
        tools=[],
        storage=storage,
        history_window=None,
        history_transform=None,
        profile_enabled=False,
    )

    # System + 2 messages in chronological order
    assert len(result) == 3
    conv_messages = result[1:]
    assert conv_messages[0]["content"] == "first"
    assert conv_messages[1]["content"] == "second"


@pytest.mark.asyncio
async def test_history_transform_with_history_window(mock_storage):
    """history_transform applied after history_window truncation."""
    storage = mock_storage
    conversation_id = "test_conv"
    user_id = "test_user"

    # Create 3 turns
    await storage.save_message(conversation_id, user_id, "user", "msg1", 1.0)
    await storage.save_message(conversation_id, user_id, "respond", "resp1", 2.0)
    await storage.save_message(conversation_id, user_id, "user", "msg2", 3.0)
    await storage.save_message(conversation_id, user_id, "respond", "resp2", 4.0)
    await storage.save_message(conversation_id, user_id, "user", "msg3", 5.0)
    await storage.save_message(conversation_id, user_id, "respond", "resp3", 6.0)

    # Track what transform receives
    received_messages = []

    async def capture_transform(messages: list[dict]) -> list[dict]:
        received_messages.extend(messages)
        return messages

    await assemble(
        user_id,
        conversation_id,
        tools=[],
        storage=storage,
        history_window=4,  # Only last 4 messages (2 turns)
        history_transform=capture_transform,
        profile_enabled=False,
    )

    # Transform should only see last 4 messages (2 turns)
    assert len(received_messages) == 4
    assert "msg3" in str(received_messages)
    assert "msg1" not in str(received_messages)


@pytest.mark.asyncio
async def test_history_transform_compression_example(mock_storage):
    """Example: compress older messages into summary."""
    storage = mock_storage
    conversation_id = "test_conv"
    user_id = "test_user"

    # Simulate long conversation
    for i in range(10):
        await storage.save_message(conversation_id, user_id, "user", f"message {i}", float(i * 2))
        await storage.save_message(
            conversation_id, user_id, "respond", f"response {i}", float(i * 2 + 1)
        )

    # Keep last 2 turns verbatim, summarize rest
    async def rolling_summary(messages: list[dict]) -> list[dict]:
        if len(messages) <= 4:  # 2 turns = 4 messages
            return messages

        recent = messages[-4:]  # Last 2 turns
        older = messages[:-4]

        # Create summary message
        summary_content = f"[Summary of {len(older)} earlier messages]"
        summary = {"role": "system", "content": summary_content}

        return [summary, *recent]

    result = await assemble(
        user_id,
        conversation_id,
        tools=[],
        storage=storage,
        history_window=None,
        history_transform=rolling_summary,
        profile_enabled=False,
    )

    # System + summary + 4 recent messages
    assert len(result) == 6
    assert "[Summary of 16 earlier messages]" in result[1]["content"]
    assert "message 9" in result[-2]["content"]
    assert "response 9" in result[-1]["content"]
