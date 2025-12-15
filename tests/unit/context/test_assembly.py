import pytest

from cogency import context


@pytest.mark.asyncio
async def test_empty_conversation(mock_config):
    messages = await context.assemble(
        "user_123",
        "conv_123",
        tools=mock_config.tools,
        storage=mock_config.storage,
        history_window=mock_config.history_window,
        profile_enabled=False,
        history_transform=None,
    )

    assert len(messages) == 1
    assert messages[0]["role"] == "system"
    assert len(messages[0]["content"]) > 0


@pytest.mark.asyncio
async def test_with_conversation(mock_config):
    storage = mock_config.storage
    await storage.save_message("conv_123", "user_123", "user", "hello")
    await storage.save_message("conv_123", "user_123", "respond", "hi there")

    messages = await context.assemble(
        "user_123",
        "conv_123",
        tools=mock_config.tools,
        storage=storage,
        history_window=mock_config.history_window,
        profile_enabled=False,
        history_transform=None,
    )

    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[1]["content"] == "hello"
    assert messages[2]["role"] == "assistant"
    assert "hi there" in messages[2]["content"]


@pytest.mark.asyncio
async def test_with_profile(mock_config):
    storage = mock_config.storage
    await storage.save_profile("user_123", {"test_key": "test_value"})

    messages = await context.assemble(
        "user_123",
        "conv_123",
        tools=mock_config.tools,
        storage=storage,
        history_window=mock_config.history_window,
        history_transform=None,
        profile_enabled=True,
    )

    assert len(messages) == 1
    assert messages[0]["role"] == "system"
    system_content = messages[0]["content"]
    assert "test_key" in system_content or "test_value" in system_content


@pytest.mark.asyncio
async def test_system_message_structure(mock_config):
    messages = await context.assemble(
        "user_123",
        "conv_123",
        tools=mock_config.tools,
        storage=mock_config.storage,
        history_window=mock_config.history_window,
        profile_enabled=False,
        history_transform=None,
        identity="Test Agent",
        instructions="Do the thing",
    )

    assert messages[0]["role"] == "system"
    system_content = messages[0]["content"]
    assert "Test Agent" in system_content
    assert "Do the thing" in system_content


@pytest.mark.asyncio
async def test_preserves_turn_structure(mock_config):
    import json

    storage = mock_config.storage
    await storage.save_message("conv_123", "user_123", "user", "debug this")
    await storage.save_message("conv_123", "user_123", "think", "checking logs")
    await storage.save_message("conv_123", "user_123", "call", '{"name": "tool", "args": {}}')
    await storage.save_message(
        "conv_123", "user_123", "result", json.dumps({"outcome": "Success", "content": "output"})
    )
    await storage.save_message("conv_123", "user_123", "respond", "done")

    messages = await context.assemble(
        "user_123",
        "conv_123",
        tools=mock_config.tools,
        storage=storage,
        history_window=None,
        profile_enabled=False,
        history_transform=None,
    )

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert messages[2]["role"] == "assistant"
    assert "<execute>" in messages[2]["content"]
    assert messages[3]["role"] == "user"
    assert messages[4]["role"] == "assistant"


@pytest.mark.asyncio
async def test_history_window(mock_config):
    storage = mock_config.storage
    await storage.save_message("conv_123", "user_123", "user", "msg1")
    await storage.save_message("conv_123", "user_123", "respond", "resp1")
    await storage.save_message("conv_123", "user_123", "user", "msg2")
    await storage.save_message("conv_123", "user_123", "respond", "resp2")
    await storage.save_message("conv_123", "user_123", "user", "msg3")
    await storage.save_message("conv_123", "user_123", "respond", "resp3")

    messages = await context.assemble(
        "user_123",
        "conv_123",
        tools=mock_config.tools,
        storage=storage,
        history_window=2,
        profile_enabled=False,
        history_transform=None,
    )

    assert len(messages) == 3
    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    assert "msg3" in messages[1]["content"]
    assert messages[2]["role"] == "assistant"
    assert "resp3" in messages[2]["content"]


@pytest.mark.asyncio
async def test_bounded_memory_loading(mock_config):
    """Verify that history_window limits database loading to avoid unbounded memory."""
    storage = mock_config.storage

    for i in range(10):
        await storage.save_message("conv_123", "user_123", "user", f"msg_{i}")
        await storage.save_message("conv_123", "user_123", "respond", f"resp_{i}")

    messages = await context.assemble(
        "user_123",
        "conv_123",
        tools=mock_config.tools,
        storage=storage,
        history_window=2,
        profile_enabled=False,
        history_transform=None,
    )

    assert messages[0]["role"] == "system"

    conversation_content = " ".join(m.get("content", "") for m in messages[1:])
    assert "msg_9" in conversation_content
    assert "resp_9" in conversation_content
    assert "msg_0" not in conversation_content
    assert "msg_1" not in conversation_content
    assert "msg_2" not in conversation_content
