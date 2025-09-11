"""Conversation history tests."""

from unittest.mock import patch

from cogency.context.constants import DEFAULT_CONVERSATION_ID, HISTORY_LIMIT
from cogency.context.conversation import history
from cogency.core.protocols import Event


@patch("cogency.context.conversation.load_messages")
def test_history(mock_load):
    """History respects limit, filters thinks, excludes current cycle, formats chronologically."""
    messages = [
        {"type": Event.USER, "content": "Past query"},
        {"type": Event.THINK, "content": "Should be filtered"},
        {
            "type": Event.CALLS,
            "content": '[{"call": {"name": "test", "args": {}}, "result": "OK"}]',
        },
        {"type": Event.RESPOND, "content": "Past response"},
        {"type": Event.USER, "content": "Current query"},  # Should be excluded
    ]
    mock_load.return_value = messages

    with patch("cogency.lib.format.format_tools", return_value="TOOLS"):
        result = history("conv_123")
        lines = [line.strip() for line in result.split("\n") if line.strip()]

        assert lines == ["USER: Past query", "TOOLS: TOOLS", "ASSISTANT: Past response"]
        assert "Should be filtered" not in result
        assert "Current query" not in result


def test_empty():
    """Ephemeral and non-existent conversations return empty."""
    assert history(DEFAULT_CONVERSATION_ID) == ""
    assert history("nonexistent") == ""


def test_constants():
    """History constants exist."""
    assert HISTORY_LIMIT == 20
    assert DEFAULT_CONVERSATION_ID == "ephemeral"
