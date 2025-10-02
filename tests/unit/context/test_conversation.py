import json

import pytest

from cogency.context import conversation


@pytest.mark.asyncio
async def test_empty_conversation(mock_storage):
    result = await conversation.history("conv_123", "user_1", mock_storage, 20)
    assert result == ""


@pytest.mark.asyncio
async def test_history_formatting(mock_storage):
    await mock_storage.save_message("conv_123", "user_1", "user", "Past question")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Past answer")
    await mock_storage.save_message("conv_123", "user_1", "user", "Current question")

    result = await conversation.history("conv_123", "user_1", mock_storage, 20)
    assert "=== HISTORY ===" in result
    assert "§user: Past question" in result
    assert "§respond: Past answer" in result
    assert "Current question" not in result


@pytest.mark.asyncio
async def test_mixed_formats(mock_storage):
    await mock_storage.save_message("conv_123", "user_1", "user", "Test mixed formats")

    call_json = json.dumps({"name": "test_tool", "args": {"msg": "hello"}})
    result_json = json.dumps({"outcome": "Success", "content": "Tool output"})
    await mock_storage.save_message("conv_123", "user_1", "call", call_json)
    await mock_storage.save_message("conv_123", "user_1", "result", result_json)

    await mock_storage.save_message(
        "conv_123", "user_1", "call", '{"name": "other_tool", "args": {}}'
    )
    await mock_storage.save_message("conv_123", "user_1", "result", "Read file.txt\nContent here")

    result = await conversation.current("conv_123", "user_1", mock_storage)
    assert '§call: {"name": "test_tool"' in result
    assert "§result: Success" in result
    assert '§call: {"name": "other_tool"' in result
    assert "§result: Read file.txt" in result


@pytest.mark.asyncio
async def test_current_cycle(mock_storage):
    await mock_storage.save_message("conv_123", "user_1", "user", "Question")
    await mock_storage.save_message("conv_123", "user_1", "think", "Reasoning")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Answer")

    await conversation.current("conv_123", "user_1", mock_storage)


@pytest.mark.asyncio
async def test_tool_formatting(mock_storage):
    await mock_storage.save_message("conv_123", "user_1", "user", "Test tools")

    call_content = json.dumps({"name": "test_tool", "args": {"param": "value"}})
    result_content = json.dumps({"outcome": "Success", "content": "Tool output"})

    await mock_storage.save_message("conv_123", "user_1", "call", call_content)
    await mock_storage.save_message("conv_123", "user_1", "result", result_content)

    result = await conversation.current("conv_123", "user_1", mock_storage)
    assert '§call: {"name": "test_tool", "args": {"param": "value"}}' in result
    assert "§result: Success" in result
    assert "Tool output" in result


@pytest.mark.asyncio
async def test_think_excluded(mock_storage):
    await mock_storage.save_message("conv_123", "user_1", "user", "Question")
    await mock_storage.save_message("conv_123", "user_1", "think", "Internal reasoning")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Answer")
    await mock_storage.save_message("conv_123", "user_1", "user", "Current")
    await mock_storage.save_message("conv_123", "user_1", "think", "Current reasoning")

    history = await conversation.history("conv_123", "user_1", mock_storage, 20)
    current = await conversation.current("conv_123", "user_1", mock_storage)

    assert "§think:" not in history
    assert "§think:" in current


@pytest.mark.asyncio
async def test_full_context_assembly(mock_storage):
    await mock_storage.save_message("conv_123", "user_1", "user", "Past")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Past answer")
    await mock_storage.save_message("conv_123", "user_1", "user", "Current")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Current answer")

    result = await conversation.full_context("conv_123", "user_1", mock_storage, 20)

    assert "=== HISTORY ===" in result
    assert "=== CURRENT ===" in result
    assert "Past" in result
    assert "Current" in result


@pytest.mark.asyncio
async def test_delimiters(mock_storage):
    await mock_storage.save_message("conv_123", "user_1", "user", "Test")
    await mock_storage.save_message("conv_123", "user_1", "think", "Think")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Respond")

    result = await conversation.current("conv_123", "user_1", mock_storage)
    lines = result.split("\n")

    # Verify exact delimiters
    assert any(line.startswith("§user:") for line in lines)
    assert any(line.startswith("§think:") for line in lines)
    assert any(line.startswith("§respond:") for line in lines)

    # Verify no alternative formats
    for line in lines:
        assert not line.startswith("user:")
        assert not line.startswith("USER:")


@pytest.mark.asyncio
async def test_edge_cases(mock_storage):
    # None conversation ID
    assert await conversation.history(None, "user_1", mock_storage, 20) == ""

    # Malformed JSON
    await mock_storage.save_message("conv_123", "user_1", "call", "not-json")
    await mock_storage.save_message("conv_123", "user_1", "user", "Current")

    result = await conversation.history("conv_123", "user_1", mock_storage, 20)
    assert "§call: not-json" in result
