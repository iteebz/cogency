"""Conversation context tests - canonical formatting specification."""

import json

import pytest

from cogency.context import conversation


@pytest.mark.asyncio
async def test_empty_conversation(mock_storage):
    """Empty conversation returns empty history."""
    result = await conversation.history("conv_123", "user_1", mock_storage, 20)
    assert result == ""


@pytest.mark.asyncio
async def test_basic_history_formatting(mock_storage):
    """History uses canonical protocol delimiters, excludes current cycle."""
    await mock_storage.save_message("conv_123", "user_1", "user", "Past question")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Past answer")
    await mock_storage.save_message("conv_123", "user_1", "user", "Current question")

    result = await conversation.history("conv_123", "user_1", mock_storage, 20)
    assert "=== HISTORY ===" in result
    assert "$user: Past question" in result
    assert "$respond: Past answer" in result
    assert "Current question" not in result


@pytest.mark.asyncio
async def test_handles_mixed_formats(mock_storage):
    """Test conversation handles both JSON arrays and string formats gracefully."""
    # Add messages with mixed call/result formats
    await mock_storage.save_message("conv_123", "user_1", "user", "Test mixed formats")

    # JSON format (expected)
    call_json = json.dumps([{"name": "test_tool", "args": {"msg": "hello"}}])
    result_json = json.dumps([{"outcome": "Success", "content": "Tool output"}])
    await mock_storage.save_message("conv_123", "user_1", "call", call_json)
    await mock_storage.save_message("conv_123", "user_1", "result", result_json)

    # String format (current accumulator output)
    await mock_storage.save_message(
        "conv_123", "user_1", "call", '{"name": "other_tool", "args": {}}'
    )
    await mock_storage.save_message("conv_123", "user_1", "result", "Read file.txt\nContent here")

    result = await conversation.current("conv_123", "user_1", mock_storage)
    assert "$call: {\"name\": \"test_tool\"" in result
    assert "$result: Success" in result
    assert "$call: {\"name\": \"other_tool\"" in result
    assert "$result: Read file.txt" in result


@pytest.mark.asyncio
async def test_current_cycle_formatting(mock_storage):
    """Current cycle includes think events, no truncation."""
    await mock_storage.save_message("conv_123", "user_1", "user", "Question")
    await mock_storage.save_message("conv_123", "user_1", "think", "Reasoning")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Answer")

    result = await conversation.current("conv_123", "user_1", mock_storage)


@pytest.mark.asyncio
async def test_tool_call_agent_formatting(mock_storage):
    """Tool calls use JSON agent format with call/result pairing."""
    await mock_storage.save_message("conv_123", "user_1", "user", "Test tools")

    call_content = json.dumps([{"name": "test_tool", "args": {"param": "value"}}])
    result_content = json.dumps([{"outcome": "Success", "content": "Tool output"}])

    await mock_storage.save_message("conv_123", "user_1", "call", call_content)
    await mock_storage.save_message("conv_123", "user_1", "result", result_content)

    result = await conversation.current("conv_123", "user_1", mock_storage)
    assert '$call: {"name": "test_tool", "args": {"param": "value"}}' in result
    assert "$result: Success" in result
    assert "Tool output" in result


@pytest.mark.asyncio
async def test_think_events_excluded_from_history(mock_storage):
    """Think events filtered from history, included in current."""
    await mock_storage.save_message("conv_123", "user_1", "user", "Question")
    await mock_storage.save_message("conv_123", "user_1", "think", "Internal reasoning")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Answer")
    await mock_storage.save_message("conv_123", "user_1", "user", "Current")
    await mock_storage.save_message("conv_123", "user_1", "think", "Current reasoning")

    history = await conversation.history("conv_123", "user_1", mock_storage, 20)
    current = await conversation.current("conv_123", "user_1", mock_storage)

    assert "$think:" not in history
    assert "$think:" in current


@pytest.mark.asyncio
async def test_full_context_assembly(mock_storage):
    """Full context combines history and current sections."""
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
async def test_protocol_delimiter_consistency(mock_storage):
    """Protocol uses exact $ prefixed delimiters."""
    await mock_storage.save_message("conv_123", "user_1", "user", "Test")
    await mock_storage.save_message("conv_123", "user_1", "think", "Think")
    await mock_storage.save_message("conv_123", "user_1", "respond", "Respond")

    result = await conversation.current("conv_123", "user_1", mock_storage)
    lines = result.split("\n")

    # Verify exact delimiters
    assert any(line.startswith("$user:") for line in lines)
    assert any(line.startswith("$think:") for line in lines)
    assert any(line.startswith("$respond:") for line in lines)

    # Verify no alternative formats
    for line in lines:
        assert not line.startswith("user:")
        assert not line.startswith("USER:")


@pytest.mark.asyncio
async def test_edge_cases(mock_storage):
    """Handle malformed JSON, missing results, empty conversations."""
    from cogency.context.constants import DEFAULT_CONVERSATION_ID

    # Default conversation ID
    assert await conversation.history(DEFAULT_CONVERSATION_ID, "user_1", mock_storage, 20) == ""

    # Malformed JSON
    await mock_storage.save_message("conv_123", "user_1", "call", "not-json")
    await mock_storage.save_message("conv_123", "user_1", "user", "Current")

    result = await conversation.history("conv_123", "user_1", mock_storage, 20)
    assert "$call: not-json" in result
