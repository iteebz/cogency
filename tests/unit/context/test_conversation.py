"""Unit tests for conversation history functionality."""

from unittest.mock import patch

from cogency.context.conversation import ConversationHistory


def test_conversation_format_recent():
    """Test conversation format for recent messages."""
    conversation = ConversationHistory()

    mock_messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"},
        {"role": "user", "content": "How are you?"},
    ]

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = mock_messages

        result = conversation.format("test_conv")

        assert "Recent conversation:" in result
        assert "user: Hello" in result
        assert "assistant: Hi there!" in result


def test_conversation_get_messages():
    """Test getting conversation messages."""
    conversation = ConversationHistory()

    mock_messages = [
        {"role": "user", "content": "Test message"},
        {"role": "assistant", "content": "Test response"},
    ]

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = mock_messages

        messages = conversation.get("test_conv")

        assert len(messages) == 2
        assert messages[0]["role"] == "user"
        assert messages[1]["role"] == "assistant"


def test_conversation_add_message():
    """Test adding messages to conversation."""
    conversation = ConversationHistory()

    with patch("cogency.context.conversation.save_conversation_message") as mock_save:
        mock_save.return_value = True

        result = conversation.add("test_conv", "user", "Hello")

        assert result is True
        mock_save.assert_called_once_with("test_conv", "user", "Hello")


def test_conversation_messages_filter_valid():
    """Test filtering valid messages for LLM context."""
    conversation = ConversationHistory()

    mock_messages = [
        {"role": "user", "content": "Valid message"},
        {"role": "assistant", "content": None},  # Invalid - null content
        {"role": None, "content": "Invalid role"},  # Invalid - null role
        {"role": "user", "content": "Another valid message"},
    ]

    with patch("cogency.context.conversation.load_conversations") as mock_load:
        mock_load.return_value = mock_messages

        messages = conversation.messages("test_conv")

        assert len(messages) == 2  # Only valid messages
        assert all(isinstance(msg.get("content"), str) for msg in messages)
        assert all(msg.get("role") for msg in messages)
